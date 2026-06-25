"""
TAI Data Recorder
=================
Records labelled BufferSnapshots for training the intent ML model.

Design rationale:
  The recorder is the feedback loop between the rule-based Phase 1 and
  the ML Phase 2. While the rule-based system runs, a human trainer
  can label the current buffer state with the correct intent. These
  labelled sequences become the training dataset.

  File format: newline-delimited JSON (NDJSON). Each line is one
  LabelledSequence serialized as a JSON object. This format is:
    - Appendable without loading the full file
    - Streamable for large datasets
    - Human-readable for debugging
    - Compatible with pandas.read_json(lines=True)

  The recorder is completely optional — if it's not used, the pipeline
  still works. It has no side effects on the pipeline itself.
"""

import json
import logging
import time
from pathlib import Path
from typing import Optional

from configs.constants import CombatIntent
from core.models import BufferSnapshot, LabelledSequence

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / "data" / "recordings"


class SequenceRecorder:

    def __init__(self, output_dir: Path = DEFAULT_OUTPUT_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._session_file: Optional[Path] = None
        self._count = 0

    def start_session(self, label: str = "") -> Path:
        """
        Open a new NDJSON file for this recording session.
        Call once at the beginning of a training session.
        """
        timestamp = int(time.time())
        name = f"session_{timestamp}_{label}.ndjson" if label else f"session_{timestamp}.ndjson"
        self._session_file = self.output_dir / name
        self._count = 0
        logger.info("Recording session started: %s", self._session_file)
        return self._session_file

    def record(
        self,
        snapshot: BufferSnapshot,
        intent_label: CombatIntent,
        notes: str = "",
    ) -> None:
        """
        Save a snapshot with its ground-truth label.
        Appends one JSON line to the current session file.
        """
        if self._session_file is None:
            self.start_session()

        labelled = LabelledSequence(
            snapshot=snapshot,
            label=intent_label,
            notes=notes,
        )

        with open(self._session_file, "a") as f:
            f.write(json.dumps(labelled.to_dict()) + "\n")

        self._count += 1
        logger.debug("Recorded sample #%d | label=%s", self._count, intent_label.name)

    @property
    def session_count(self) -> int:
        return self._count

    def load_session(self, path: Path) -> list:
        """Load a session file back into a list of dicts for inspection."""
        records = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records
