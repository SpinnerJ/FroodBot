import os
import logging
from transformers import GPT2LMHeadModel, GPT2Tokenizer, TextDataset, DataCollatorForLanguageModeling
from transformers import Trainer, TrainingArguments
from data_handler import DataHandler


class AIHandler:
    def __init__(self, base_path):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.base_path = base_path
        self.model = GPT2LMHeadModel.from_pretrained("gpt2")
        self.tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
        # Set pad_token_id to eos_token_id if it's not already set
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
        self.data_handler = DataHandler(base_path)

    def generate_response(self, input_text):
        try:
            inputs = self.tokenizer.encode(input_text, return_tensors='pt')
            attention_mask = inputs.ne(self.tokenizer.pad_token_id).float()
            outputs = self.model.generate(
                inputs,
                max_length=50,
                num_return_sequences=1,
                attention_mask=attention_mask,
                pad_token_id=self.tokenizer.eos_token_id,
                do_sample=True,
                top_k=50,
                temperature=0.7
            )
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return response
        except Exception as e:
            self.logger.error(f"Error in generating response: {e}")
            raise

    def preprocess_and_train(self, key, num_epochs=3, batch_size=2):
        safe_key = self.data_handler._sanitize_key(key)
        model_path = f"./gpt2-finetuned/{safe_key}"
        if os.path.exists(model_path):
            self.model = GPT2LMHeadModel.from_pretrained(model_path)
            self.logger.info("Loaded existing model.")
        else:
            try:
                self.data_handler.preprocess_data(key)
                input_file = os.path.join(self.data_handler.base_path, f'{safe_key}_preprocessed.txt')
                if not os.path.exists(input_file):
                    self.logger.error(f"Preprocessed data file not found: {input_file}")
                    return

                train_dataset = TextDataset(
                    tokenizer=self.tokenizer,
                    file_path=input_file,
                    block_size=128
                )
                data_collator = DataCollatorForLanguageModeling(
                    tokenizer=self.tokenizer, mlm=False
                )
                training_args = TrainingArguments(
                    output_dir=model_path,
                    overwrite_output_dir=True,
                    num_train_epochs=num_epochs,
                    per_device_train_batch_size=batch_size,
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
                self.model.save_pretrained(model_path)
                self.logger.info("Model trained and saved successfully.")
            except Exception as e:
                self.logger.error(f"Error in model training: {e}")
                raise
