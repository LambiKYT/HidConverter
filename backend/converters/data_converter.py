import os
import json
import csv
import io
import logging
from xml.etree import ElementTree as ET
from typing import Dict, List

from .base import BaseConverter

logger = logging.getLogger("hidconverter")

try:
    import yaml
except ImportError:
    yaml = None


def _xml_to_dict(element):
    result = {}
    for child in element:
        tag = child.tag
        sub = _xml_to_dict(child)
        text = (child.text or "").strip()
        if sub:
            value = sub
        else:
            value = text
        if tag in result:
            if not isinstance(result[tag], list):
                result[tag] = [result[tag]]
            result[tag].append(value)
        else:
            result[tag] = value
    return result


def _dict_to_xml(tag, data):
    elem = ET.Element(tag)
    if isinstance(data, dict):
        for key, val in data.items():
            child = _dict_to_xml(key, val)
            elem.append(child)
    elif isinstance(data, list):
        for item in data:
            child = _dict_to_xml(tag, item)
            elem.append(child)
    else:
        elem.text = str(data)
    return elem


class DataConverter(BaseConverter):
    SUPPORTED = {
        "json": ["yaml", "xml", "csv"],
        "yaml": ["json"],
        "yml":  ["json"],
        "xml":  ["json"],
        "csv":  ["json"],
    }

    def supported_conversions(self) -> Dict[str, List[str]]:
        return self.SUPPORTED

    def convert(self, file_path: str, target_format: str, output_dir: str, **kwargs) -> str:
        ext = os.path.splitext(file_path)[1].lstrip(".").lower()
        if ext not in self.SUPPORTED or target_format not in self.SUPPORTED[ext]:
            raise ValueError(f"Conversion from {ext} to {target_format} is not supported")

        output_path = self.get_output_path(file_path, target_format, output_dir)
        func_name = f"_convert_{ext}_to_{target_format}"
        handler = getattr(self, func_name, None)
        if not handler:
            raise ValueError(f"No handler for {ext} -> {target_format}")

        return handler(file_path, output_path)

    # --- JSON -> YAML ---

    def _convert_json_to_yaml(self, file_path: str, output_path: str) -> str:
        if yaml is None:
            raise RuntimeError("Missing dependency: pyyaml")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        return output_path

    # --- JSON -> XML ---

    def _convert_json_to_xml(self, file_path: str, output_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        root = _dict_to_xml("root", data)
        tree = ET.ElementTree(root)
        tree.write(output_path, encoding="utf-8", xml_declaration=True)
        return output_path

    # --- JSON -> CSV ---

    def _convert_json_to_csv(self, file_path: str, output_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            data = [data]

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            if data and isinstance(data[0], dict):
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            else:
                writer = csv.writer(f)
                for row in data:
                    writer.writerow([row] if not isinstance(row, list) else row)
        return output_path

    # --- YAML -> JSON ---

    def _convert_yaml_to_json(self, file_path: str, output_path: str) -> str:
        if yaml is None:
            raise RuntimeError("Missing dependency: pyyaml")

        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return output_path

    _convert_yml_to_json = _convert_yaml_to_json

    # --- XML -> JSON ---

    def _convert_xml_to_json(self, file_path: str, output_path: str) -> str:
        tree = ET.parse(file_path)
        data = _xml_to_dict(tree.getroot())
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return output_path

    # --- CSV -> JSON ---

    def _convert_csv_to_json(self, file_path: str, output_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            data = [row for row in reader]

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return output_path
