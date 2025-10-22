import json
import re
from urllib.parse import unquote

def normalize_request(log_line: str) -> str:
    """
    Takes a raw JSON log line and returns a single, normalized string.
    """
    try:
        log_data = json.loads(log_line)

        method = log_data.get("method", "-")
        uri = log_data.get("uri", "-")
        args = log_data.get("args", "-")
        body = log_data.get("body", "-")

        full_request_str = f"{method} {uri} {args} {body}"

        # --- Decode URL ---
        decoded_str = unquote(full_request_str)

        # --- Normalization ---
        # 1. Normalize all numbers to <NUM>
        normalized = re.sub(r'\d+', ' <NUM> ', decoded_str)

        # 2. Normalize search queries
        normalized = re.sub(r'search_query=[a-zA-Z]+', 'search_query=<STR>', normalized)

        # 3. Normalize chatbot queries
        normalized = re.sub(r'{"query": ".*"}', '{"query": "<STR>"}', normalized, flags=re.DOTALL)

        # 4. (NEW) Normalize OTP requests
        normalized = re.sub(r'{"phone_number": "\+\ <NUM>\ \ <NUM>\ "}', '{"phone_number": "<PHONE>"}', normalized)

        # 5. (NEW) Normalize SignUp requests
        # This regex is complex, but it looks for the signup JSON structure
        normalized = re.sub(
            r'{"user_name": "user_ <NUM>\ ", "phone_number": "\+\ <NUM>\ \ <NUM>\ ", "email": "user_ <NUM>\ @example.com", "full_name": "Test User\ <NUM>\ "}',
            '{"user_name": "<STR>", "phone_number": "<PHONE>", "email": "<EMAIL>", "full_name": "<STR>"}',
            normalized,
            flags=re.DOTALL
        )

        # Clean up extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        return normalized

    except json.JSONDecodeError as e:
        print(f"!!! JSONDecodeError on line: '{log_line}'")
        print(f"!!! Error: {e}")
        return ""

# This is our main script.
if __name__ == "__main__":
    input_file = "all_logs.json"
    output_file = "training_data.txt"

    print(f"--- Normalizing all logs from {input_file} ---")

    processed_count = 0
    skipped_count = 0

    try:
        # Open the input file with "utf-16" encoding.
        with open(input_file, "r", encoding="utf-16") as f_in, \
             open(output_file, "w", encoding="utf-8") as f_out:

            for line in f_in:
                stripped_line = line.strip()
                if not stripped_line:
                    skipped_count += 1
                    continue

                normalized_output = normalize_request(stripped_line)

                if normalized_output:
                    f_out.write(normalized_output + "\n")
                    processed_count += 1
                else:
                    skipped_count += 1

        print(f"\n--- SUCCESS ---")
        print(f"✅ Processed {processed_count} log lines.")
        print(f"⚠️ Skipped {skipped_count} broken/empty log lines.")
        print(f"Clean training data saved to: {output_file}")

    except FileNotFoundError:
        print(f"\n[ERROR] {input_file} file not found!")
        print("Run this command first:")
        print("docker exec my-waf-server cat /var/log/nginx/waf_stream.log > all_logs.json")