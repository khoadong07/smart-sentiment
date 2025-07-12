from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from litserve import LitAPI, LitServer

class BERTLitAPI(LitAPI):
    def setup(self, device):
        """
        Load the tokenizer and model from custom Hugging Face repo
        """
        model_name = "Khoa/sentiment-analysis-all-category-122024.8"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.to(device)
        self.model.eval()
        raw_id2label = {int(k): v for k, v in self.model.config.id2label.items()}
        label_alias = {
            "NEG": "Negative",
            "POS": "Positive",
            "NEU": "Neutral"
        }

        self.id2label = {
            idx: label_alias.get(label.upper(), label)
            for idx, label in raw_id2label.items()
        }
    def decode_request(self, request):
        text = request["text"]
        if isinstance(text, str):
            text = [text]
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        return inputs

    def predict(self, inputs):
        with torch.no_grad():
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            outputs = self.model(**inputs)
        return outputs.logits

    def encode_response(self, logits):
        probs = torch.nn.functional.softmax(logits, dim=-1)
        top_probs, top_classes = torch.topk(probs, k=1, dim=-1)

        results = []
        for i in range(len(top_classes)):
            class_idx = top_classes[i].item()
            result = {
                "predicted_class": class_idx,
                "predicted_label": self.id2label.get(class_idx, str(class_idx)),
                "confidence": top_probs[i].item(),
                "all_probs": {
                    self.id2label.get(j, str(j)): round(probs[i][j].item(), 4)
                    for j in range(probs.size(1))
                }
            }
            results.append(result)

        return results if len(results) > 1 else results[0]

if __name__ == "__main__":
    api = BERTLitAPI()
    server = LitServer(api, accelerator='cpu', devices=0)
    server.run(port=8000, num_api_servers=8)