from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    category: str
    origin: str
    description: str
    expected_first_boundary: str | None
    expected_classification: str | None
    candidate_implementation: str
    reference_implementation: str = "paritylens/pipelines/reference.py"
    fixture_set: str = "synthetic-v1"

    def metadata(self) -> dict:
        return asdict(self)


SCENARIOS = {
    s.id: s for s in (
        Scenario("historical_rgb_bgr", "RGB/BGR channel order", "channel_order", "historical",
                 "Exact pre-repair Git snapshot, executed on additional synthetic inputs.",
                 "decode", "channel_order_mismatch", "demo/candidate_before_bob.py"),
        Scenario("scaling_mismatch", "Scaling mismatch", "scaling", "controlled_evaluation",
                 "RGB decode is correct; scaling keeps float32 values in 0..255 instead of dividing by 255.",
                 "scaling", "scaling_mismatch", "evaluation/candidates.py"),
        Scenario("normalization_mismatch", "Normalization mismatch", "normalization", "controlled_evaluation",
                 "Earlier stages match; normalization uses fixed mean [0.5, 0.5, 0.5] and std [0.5, 0.5, 0.5].",
                 "normalization", "normalization_mismatch", "evaluation/candidates.py"),
        Scenario("clean_control", "Clean control", "control", "controlled_evaluation",
                 "Independent Pillow reference and current RGB-correct OpenCV candidate, with no injected defect.",
                 None, None, "paritylens/pipelines/candidate.py"),
    )
}


def get_scenario(scenario_id: str) -> Scenario:
    if scenario_id not in SCENARIOS:
        raise ValueError("Unsupported evaluation scenario")
    return SCENARIOS[scenario_id]
