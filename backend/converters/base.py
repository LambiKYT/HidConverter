from abc import ABC, abstractmethod
from typing import Dict, List


class BaseConverter(ABC):
    @abstractmethod
    def convert(self, file_path: str, target_format: str, output_dir: str) -> str:
        ...

    @abstractmethod
    def supported_conversions(self) -> Dict[str, List[str]]:
        ...

    def get_output_path(self, file_path: str, target_format: str, output_dir: str) -> str:
        import os
        base = os.path.splitext(os.path.basename(file_path))[0]
        return os.path.join(output_dir, f"{base}.{target_format}")
