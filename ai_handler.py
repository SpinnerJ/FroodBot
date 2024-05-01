from transformers import GPT2LMHeadModel, GPT2Tokenizer, TextDataset, DataCollatorForLanguageModeling
from transformers import Trainer, TrainingArguments
import os
from data_handler import DataHandler


class AIHandler:
    def __init__(self, base_path):
        self.model = GPT2LMHeadModel.from_pretrained("gpt2")
        self.tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
        self.data_handler = DataHandler(base_path)

    def generate_response(self, input_text):
        inputs = self.tokenizer.encode(input_text, return_tensors='pt')

        # Set pad_token_id to eos_token_id if it's not already set
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

        # Create attention mask
        attention_mask = inputs.ne(self.tokenizer.pad_token_id).float()

        outputs = self.model.generate(
            inputs,
            max_length=50,
            num_return_sequences=1,
            attention_mask=attention_mask,  # Pass attention mask to the generate method
            pad_token_id=self.tokenizer.eos_token_id,  # Set pad_token_id to eos_token_id
            do_sample=True,  # Enable sampling
            top_k=50,  # Set the number of highest probability vocabulary tokens to keep for top-k-filtering
            temperature=0.7  # Set the temperature
        )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response

    def preprocess_and_train(self, key):
        model_path = f"./gpt2-finetuned/{key}"

        # Check if a trained model already exists for the user
        if os.path.exists(model_path):
            # Load the existing model
            self.model = GPT2LMHeadModel.from_pretrained(model_path)
        else:
            # Preprocess the data and train a new model
            self.data_handler.preprocess_data(key)
            safe_key = self.data_handler._sanitize_key(key)
            input_file = os.path.join(self.data_handler.base_path, f'{safe_key}_preprocessed.txt')

            train_dataset = TextDataset(
                tokenizer=self.tokenizer,
                file_path=input_file,
                block_size=128)

            data_collator = DataCollatorForLanguageModeling(
                tokenizer=self.tokenizer, mlm=False)

            training_args = TrainingArguments(
                output_dir="./gpt2-finetuned",
                overwrite_output_dir=True,
                num_train_epochs=3,
                per_device_train_batch_size=2,
                save_steps=10_000,
                save_total_limit=2,
            )

            trainer = Trainer(
                model=self.model,
                args=training_args,
                data_collator=data_collator,
                train_dataset=train_dataset,
            )

            trainer.train()

            # Save the trained model with the key
            model_path = f"./gpt2-finetuned/{key}"
            self.model.save_pretrained(model_path)

