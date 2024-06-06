import importlib.util

_sentence_transformers = importlib.util.find_spec("sentence_transformers") is not None


def is_sentence_transformers_available():
    return _sentence_transformers


if is_sentence_transformers_available():
    from sentence_transformers import CrossEncoder, SentenceTransformer, util


class SentenceSimilarityPipeline:
    def __init__(self, model_dir: str, device: str = None):  # needs "cuda" for GPU
        self.model = SentenceTransformer(model_dir, device=device)

    def __call__(self, inputs=None):
        embeddings1 = self.model.encode(
            inputs["source_sentence"], convert_to_tensor=True
        )
        embeddings2 = self.model.encode(inputs["sentences"], convert_to_tensor=True)
        similarities = util.pytorch_cos_sim(embeddings1, embeddings2).tolist()[0]
        return {"similarities": similarities}


class SentenceEmbeddingPipeline:
    def __init__(self, model_dir: str, device: str = None):  # needs "cuda" for GPU
        self.model = SentenceTransformer(model_dir, device=device)

    def __call__(self, inputs):
        embeddings = self.model.encode(inputs).tolist()
        return {"embeddings": embeddings}


class RankingPipeline:
    def __init__(self, model_dir: str, device: str = None):  # needs "cuda" for GPU
        self.model = CrossEncoder(model_dir, device=device)

    def __call__(self, inputs, parameters=None):
        parameters = parameters or {"return_documents": False}

        if isinstance(inputs, list):
            scores = self.model.predict(inputs).tolist()
            return {"scores": scores}
        else:
            _scores = self.model.rank(
                inputs["query"],
                inputs["texts"],
                return_documents=parameters["return_documents"],
            )
            # rename "corpus_id" key to "index" for all scores to match TEI
            scores = []
            for score in scores:
                score["index"] = score.pop("corpus_id")
                scores.append(score)

            return scores


SENTENCE_TRANSFORMERS_TASKS = {
    "sentence-similarity": SentenceSimilarityPipeline,
    "sentence-embeddings": SentenceEmbeddingPipeline,
    "sentence-ranking": RankingPipeline,
}


def get_sentence_transformers_pipeline(task=None, model_dir=None, device=-1, **kwargs):
    device = "cuda" if device == 0 else "cpu"
    pipeline = SENTENCE_TRANSFORMERS_TASKS[task](model_dir=model_dir, device=device)
    return pipeline
