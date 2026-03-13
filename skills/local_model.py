import os
import json
import threading
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from huggingface_hub import snapshot_download, HfApi
import logging

logger = logging.getLogger(__name__)

class LocalModelManager:
    """
    Manages local Hugging Face models: download, load, generate, delete.
    """
    # Recommended models with metadata
    AVAILABLE_MODELS = [
        {
            "id": "distilgpt2",
            "name": "DistilGPT2",
            "description": "Small, fast text generation",
            "size": "~350 MB",
            "requires_gpu": False,
            "repo_id": "distilgpt2"
        },
        {
            "id": "microsoft/phi-2",
            "name": "Phi-2",
            "description": "2.7B parameter model, good for reasoning",
            "size": "~5 GB",
            "requires_gpu": True,
            "repo_id": "microsoft/phi-2"
        },
        {
            "id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            "name": "TinyLlama Chat",
            "description": "1.1B parameter chat model",
            "size": "~2.2 GB",
            "requires_gpu": False,
            "repo_id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        }
    ]

    def __init__(self, models_dir="models"):
        self.models_dir = models_dir
        self.downloaded_dir = os.path.join(models_dir, "downloaded")
        self.manifest_path = os.path.join(models_dir, "manifest.json")
        self.manifest = self._load_manifest()
        self.current_model_id = self.manifest.get("active_model")
        self.current_model = None
        self.current_tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        os.makedirs(self.downloaded_dir, exist_ok=True)

    def _load_manifest(self):
        if os.path.exists(self.manifest_path):
            with open(self.manifest_path, 'r') as f:
                return json.load(f)
        return {"downloaded": {}, "active_model": None}

    def _save_manifest(self):
        with open(self.manifest_path, 'w') as f:
            json.dump(self.manifest, f, indent=2)

    def list_available(self):
        """Return list of predefined models with download status."""
        result = []
        for model in self.AVAILABLE_MODELS:
            status = "downloaded" if model["repo_id"] in self.manifest["downloaded"] else "available"
            result.append({**model, "status": status})
        return result

    def download_model(self, repo_id, callback=None):
        """
        Download model from Hugging Face hub into downloaded_dir.
        Runs in a thread to avoid blocking.
        """
        def _download():
            try:
                logger.info(f"Downloading {repo_id}...")
                # Use snapshot_download to get full repo
                local_dir = os.path.join(self.downloaded_dir, repo_id.replace("/", "_"))
                snapshot_download(repo_id=repo_id, local_dir=local_dir, local_dir_use_symlinks=False)
                # Update manifest
                self.manifest["downloaded"][repo_id] = {
                    "path": local_dir,
                    "status": "downloaded"
                }
                self._save_manifest()
                logger.info(f"Downloaded {repo_id} to {local_dir}")
                if callback:
                    callback(True, repo_id)
            except Exception as e:
                logger.error(f"Download failed: {e}")
                if callback:
                    callback(False, repo_id, str(e))

        thread = threading.Thread(target=_download)
        thread.start()
        return thread

    def load_model(self, repo_id):
        """Load model and tokenizer into memory."""
        if repo_id not in self.manifest["downloaded"]:
            raise ValueError(f"Model {repo_id} not downloaded")
        model_info = self.manifest["downloaded"][repo_id]
        model_path = model_info["path"]

        logger.info(f"Loading model {repo_id} from {model_path} on {self.device}")
        self.current_tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.current_model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None
        ).to(self.device)
        self.current_model_id = repo_id
        self.manifest["active_model"] = repo_id
        self._save_manifest()
        logger.info(f"Model {repo_id} loaded")

    def unload_model(self):
        """Free memory by deleting model reference."""
        self.current_model = None
        self.current_tokenizer = None
        self.current_model_id = None
        self.manifest["active_model"] = None
        self._save_manifest()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("Model unloaded")

    def generate(self, prompt, max_new_tokens=200, temperature=0.7, **kwargs):
        """Generate text using currently loaded model."""
        if self.current_model is None or self.current_tokenizer is None:
            raise RuntimeError("No model loaded")
        inputs = self.current_tokenizer(prompt, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = self.current_model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=True,
                pad_token_id=self.current_tokenizer.eos_token_id,
                **kwargs
            )
        return self.current_tokenizer.decode(outputs[0], skip_special_tokens=True)

    def delete_model(self, repo_id):
        """Remove model files and update manifest."""
        if repo_id not in self.manifest["downloaded"]:
            return False
        model_path = self.manifest["downloaded"][repo_id]["path"]
        # Remove files
        import shutil
        shutil.rmtree(model_path, ignore_errors=True)
        # Update manifest
        del self.manifest["downloaded"][repo_id]
        if self.current_model_id == repo_id:
            self.unload_model()
        self._save_manifest()
        return True