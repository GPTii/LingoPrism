from django.db import models


class AlgorithmConfig(models.Model):
    """Which self-implemented algorithm the system uses (one row). Changed from the admin "Thuật toán" page."""

    class Scheduler(models.TextChoices):
        LEITNER = "leitner", "Leitner (SnapLingua cũ)"
        SM2 = "sm2", "SM-2"
        FSRS = "fsrs", "FSRS"

    class Priority(models.TextChoices):
        DUE = "due", "Theo hạn ôn (baseline)"
        VIP = "vip", "VIP – ưu tiên theo nhầm lẫn thị giác"

    class Distractor(models.TextChoices):
        RANDOM = "random", "Ngẫu nhiên cùng chủ đề (baseline)"
        SMART = "smart", "Smart Distractor (Word2Vec)"

    class Proximity(models.TextChoices):
        POSTGRES = "postgres", "PostgreSQL earthdistance (baseline)"
        GRID = "grid", "Grid index tự cài + Haversine"

    scheduler = models.CharField(max_length=8, choices=Scheduler.choices, default=Scheduler.SM2)
    review_priority = models.CharField(max_length=4, choices=Priority.choices, default=Priority.VIP)
    distractor = models.CharField(max_length=6, choices=Distractor.choices, default=Distractor.SMART)
    proximity = models.CharField(max_length=8, choices=Proximity.choices, default=Proximity.GRID)
    fsrs_weights = models.JSONField(default=list, blank=True, help_text="Trống = tham số mặc định FSRS-4.5; GA có thể ghi đè")
    vip_weights = models.JSONField(default=dict, blank=True)
    desired_retention = models.FloatField(default=0.9)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get(cls) -> "AlgorithmConfig":
        return cls.objects.get_or_create(pk=1)[0]


class ExperimentRun(models.Model):
    """Results of one experiment (evaluation of an algorithm against its baseline), shown on the admin page."""

    kind = models.CharField(max_length=20, db_index=True)  # srs | vip | distractor | proximity | ga | word2vec
    results = models.JSONField(default=dict)
    duration_s = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
