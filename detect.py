import torch
import json
import time
import subprocess # To run 'docker exec tail'

# --- Import from our existing files ---
from transformers import DistilBertTokenizer, DistilBertForMaskedLM
from normalize import normalize_request # Import our cleanup function

# --- Configuration ---
MODEL_PATH = "./waf_model" # Where we saved our trained model
LOG_FILE_IN_CONTAINER = "/var/log/nginx/waf_stream.log"
CONTAINER_NAME = "my-waf-server"

# --- Anomaly Threshold ---
# This is the CRITICAL value. How "surprised" does the model need to be?
# You find this value by testing known good vs. known bad requests.
# Start with a value like 5.0 and adjust based on testing.
# Lower value = More sensitive (more alerts, maybe false positives)
# Higher value = Less sensitive (fewer alerts, maybe misses)
ANOMALY_THRESHOLD = 5.0

def get_anomaly_score(model, tokenizer, normalized_text: str) -> float:
    """
    Calculates the model's "surprise" (loss) for a given request string.
    A high loss means the model found the request unusual -> Anomaly.
    """
    # We don't need gradients during inference
    with torch.no_grad():
        # 1. Tokenize the input text
        inputs = tokenizer(
            normalized_text,
            return_tensors='pt', # Return PyTorch tensors
            truncation=True,
            max_length=128,    # Must match the training max_length
            padding='max_length' # Must match the training padding
        )

        # Move tensors to the CPU (since we trained on CPU)
        inputs = {k: v.to("cpu") for k, v in inputs.items()}

        # 2. Feed inputs AND labels to the MaskedLM model
        # The model will internally create masks and calculate the loss
        # based on how well it could predict the original tokens.
        outputs = model(**inputs, labels=inputs.input_ids)

        # 3. This loss value IS our anomaly score!
        return outputs.loss.item()

def tail_docker_log(container_name, log_file):
    """
    Continuously tails the log file inside the Docker container
    and yields new lines as they appear.
    Uses 'docker exec tail -F -n 0'
    """
    print(f"--- Tailing log file '{log_file}' in container '{container_name}' ---")
    # -F: Follow the file name (handles log rotation)
    # -n 0: Start from the end (don't show old logs)
    process = subprocess.Popen(
        ["docker", "exec", container_name, "tail", "-F", "-n", "0", log_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True, # Decode output as text
        errors='replace' # Handle potential encoding errors
    )

    try:
        while True:
            line = process.stdout.readline()
            if not line:
                # Check if process exited unexpectedly
                if process.poll() is not None:
                    print("\n[ERROR] Docker tail process stopped.")
                    stderr_output = process.stderr.read()
                    if stderr_output:
                         print(f"Stderr: {stderr_output}")
                    break
                time.sleep(0.1) # Wait briefly if no new line
                continue
            yield line.strip() # Return the new line, cleaned up
    except KeyboardInterrupt:
        print("\n--- Stopping log tailing ---")
    finally:
        process.terminate() # Ensure the tail process is stopped

if __name__ == "__main__":
    print("--- WAF Anomaly Detector Starting ---")

    print(f"1. Loading model and tokenizer from {MODEL_PATH}...")
    try:
        model = DistilBertForMaskedLM.from_pretrained(MODEL_PATH).to("cpu") # Load to CPU
        tokenizer = DistilBertTokenizer.from_pretrained(MODEL_PATH)
        model.eval() # Set model to evaluation mode (important!)
        print("   Model loaded successfully.")
    except Exception as e:
        print(f"\n[ERROR] Failed to load model/tokenizer from {MODEL_PATH}")
        print(f"Did training complete successfully? Does the folder exist?")
        print(f"Error details: {e}")
        exit() # Stop if model can't load

    print("\n2. Starting real-time log monitoring...")
    print(f"   Anomaly threshold set to: {ANOMALY_THRESHOLD}")
    print("   (Press Ctrl+C to stop)")

    log_lines = tail_docker_log(CONTAINER_NAME, LOG_FILE_IN_CONTAINER)

    for log_line in log_lines:
        if not log_line:
            continue

        try:
            # 1. Normalize the raw log line
            normalized_req = normalize_request(log_line)
            if not normalized_req: # Skip if normalization failed
                continue

            # 2. Get the anomaly score from the model
            score = get_anomaly_score(model, tokenizer, normalized_req)

            # 3. Check against the threshold
            if score > ANOMALY_THRESHOLD:
                print(f"\n🚨 [ANOMALY DETECTED] Score: {score:.4f}")
                print(f"   Raw Log: {log_line}")
                print(f"   Normalized: {normalized_req}")
            else:
                # Optional: Print scores for normal traffic to help tune threshold
                # print(f"[Normal] Score: {score:.4f} | Norm: {normalized_req[:50]}...")
                pass # Don't print anything for normal requests

        except Exception as e:
            print(f"\n[ERROR] Could not process log line: {log_line}")
            print(f"Error details: {e}")

    print("--- WAF Anomaly Detector Shutting Down ---")