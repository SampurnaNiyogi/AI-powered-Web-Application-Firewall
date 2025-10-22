import os
import torch
from transformers import (
    DistilBertTokenizer, 
    DistilBertForMaskedLM,
    DataCollatorForLanguageModeling,
    Trainer, 
    TrainingArguments
)
from datasets import load_dataset

# --- 1. Configuration ---

# The pre-trained model we'll use. 
# 'distilbert-base-uncased' is small, fast, and perfect for this.
MODEL_NAME = "distilbert-base-uncased"

# The file we created in the last step
TRAINING_FILE = "training_data.txt"

# Where we'll save our new, trained model
OUTPUT_DIR = "./waf_model"


def train_model():
    print(f"--- 1. Loading Tokenizer ({MODEL_NAME}) ---")
    # The tokenizer turns our text strings into number-tokens the AI understands
    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_NAME)

    print(f"--- 2. Loading and Tokenizing Dataset ({TRAINING_FILE}) ---")
    # Load the dataset from our text file
    dataset = load_dataset('text', data_files={'train': TRAINING_FILE})

    # Define the function that tokenizes our text
    def tokenize_function(examples):
        # This will truncate/pad all logs to be the same length (128 tokens)
        return tokenizer(
            examples['text'], 
            truncation=True, 
            padding='max_length', 
            max_length=128
        )

    # Apply the tokenization to our entire dataset
    tokenized_dataset = dataset.map(tokenize_function, batched=True)

    print(f"--- 3. Loading Pre-trained Model ({MODEL_NAME}) ---")
    # Load the "Masked Language Model" (MLM) version of DistilBERT.
    # This is the "fill-in-the-blank" model.
    model = DistilBertForMaskedLM.from_pretrained(MODEL_NAME)

    print("--- 4. Setting up Data Collator ---")
    # This is the "magic" part.
    # It automatically takes our data and creates the "fill-in-the-blank" game.
    # It will randomly hide (mask) 15% of the tokens in each request.
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer, 
        mlm=True, 
        mlm_probability=0.15
    )

    print("--- 5. Setting up Training Arguments ---")
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,          # Where to save the model
        overwrite_output_dir=True,      # Overwrite old models
        num_train_epochs=50,            # How many times to loop over the data (50 is good for a small dataset)
        per_device_train_batch_size=8,  # How many logs to process at once
        save_steps=10_000,              # How often to save checkpoints (we won't need this)
        save_total_limit=2,             # Keep only the last 2 checkpoints
    )

    print("--- 6. Creating the Trainer ---")
    # The Trainer object bundles everything together
    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=data_collator,
        train_dataset=tokenized_dataset['train'],
    )

    print("\n--- 7. STARTING MODEL TRAINING ---")
    print("This may take a few minutes...")

    # This is the command that starts the training!
    trainer.train()

    print("--- 8. TRAINING COMPLETE ---")

    # Save our final, smart model and the tokenizer to the output directory
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"✅ Model saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    # Check if a GPU is available (training is MUCH faster on a GPU)
    if torch.cuda.is_available():
        print("GPU (CUDA) is available! Training will be fast.")
    else:
        print("No GPU (CUDA) detected. Training will run on the CPU (this may be slow).")

    train_model()