"""Train the self-implemented Word2Vec on Tatoeba English sentences and store one vector per vocabulary concept."""
import time

import numpy as np
from django.core.management.base import BaseCommand

from apps.algorithms import word2vec
from apps.algorithms.distractor import VECTORS
from apps.algorithms.models import ExperimentRun
from apps.vocab.management.commands import import_tatoeba as tat
from apps.vocab.models import Word, WordTranslation


class Command(BaseCommand):
    help = "Huấn luyện Word2Vec (skip-gram + negative sampling, tự cài bằng NumPy) cho Smart Distractor"

    def add_arguments(self, parser):
        parser.add_argument("--sentences", type=int, default=2000000)
        parser.add_argument("--epochs", type=int, default=5)
        parser.add_argument("--dim", type=int, default=100)

    def handle(self, *args, sentences, epochs, dim, **opts):
        t0 = time.time()
        rng = np.random.default_rng(0)
        rows = [r[2] for r in tat._rows("eng_sentences_detailed.tsv.bz2") if len(r) >= 3]
        pick = rng.choice(len(rows), size=min(sentences, len(rows)), replace=False)
        corpus = [word2vec.tokenize(rows[i]) for i in pick]
        self.stdout.write(f"Corpus: {len(corpus):,} câu tiếng Anh (Tatoeba)")
        index, vecs = word2vec.train(corpus, dim=dim, epochs=epochs, log=self.stdout.write)
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        unit = vecs / np.where(norms == 0, 1, norms)
        slugs, out = [], []
        en = dict(WordTranslation.objects.filter(language_id="en").values_list("word_id", "text"))
        for w in Word.objects.all():
            v = word2vec.phrase_vector(en.get(w.id, w.slug.replace("-", " ")), index, vecs)
            if v is not None:
                slugs.append(w.slug)
                out.append(v.astype(np.float32))
        np.savez_compressed(VECTORS, slugs=np.array(slugs), vectors=np.stack(out))
        # sanity check shown on the admin page: nearest neighbours of a few words
        probes = {}
        for q in ["cat", "apple", "teacher", "bus", "red", "happy", "rain", "doctor"]:
            if q in index:
                sims = unit @ unit[index[q]]
                probes[q] = [list(index)[i] for i in np.argsort(-sims)[1:7]]
        res = {"sentences": len(corpus), "vocab": len(index), "dim": dim, "epochs": epochs,
               "concepts_with_vector": len(slugs), "concepts_total": Word.objects.count(), "neighbours": probes}
        ExperimentRun.objects.create(kind="word2vec", results=res, duration_s=time.time() - t0)
        self.stdout.write(self.style.SUCCESS(f"Đã lưu {len(slugs)} vector khái niệm → {VECTORS.name} ({time.time() - t0:.0f}s)"))
        for q, nn in probes.items():
            self.stdout.write(f"  {q}: {', '.join(nn)}")
