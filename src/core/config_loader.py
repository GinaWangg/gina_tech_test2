# config_loader.py
from pathlib import Path
from typing import Any, Dict, Optional, List, Mapping
import os
from types import MappingProxyType

# dotenv==0.9.9 套件
from dotenv import load_dotenv


APP_ENV = os.getenv("TECH_APP_ENV", "dev").lower()  ## 根據不同環境設定你需要的讀取的檔案 參考下面圖片
IS_CLOUD = bool(os.getenv("SCM_DO_BUILD_DURING_DEPLOYMENT"))
_CONFIG_DIR = None
if not IS_CLOUD:
    env_file = Path(rf"\\TP-TABLEAU-V05\DSTeam\ResourceNSharing\8.gitLab env資訊\tech_agent\env\.env.{APP_ENV}")  # 讀取共編資料夾 避免代理交接共同開發時候漏掉
    if env_file.exists():
        load_dotenv(env_file, override=True)
    # 以 CONFIG_DIR 作為相對路徑基準（預設目前工作目錄）
    _CONFIG_DIR = Path(rf"\\TP-TABLEAU-V05\DSTeam\ResourceNSharing\8.gitLab env資訊\tech_agent\configs").resolve()

# 對外暴露的唯讀環境快照（避免被各模組修改）
config: Dict[str, str] = MappingProxyType(dict(os.environ))
# print(config)


# ---- 基本取值 ----
def getenv(key: str, default: Optional[str] = None) -> Optional[str]:
    """取得環境變數（字串）。若不存在回傳 default。"""
    return config.get(key, default)

def require(key: str) -> str:
    """取必填環境變數，缺少即拋出 KeyError。"""
    val = config.get(key)
    if val is None:
        raise KeyError(f"Missing required env: {key}")
    return val


# ---- 常用轉型 ----
def getenv_int(key: str, default: Optional[int] = None) -> Optional[int]:
    v = config.get(key)
    if v is None:
        return default
    try:
        return int(v.strip())
    except ValueError:
        raise ValueError(f"Env {key} should be int, got: {v!r}")

def getenv_bool(key: str, default: Optional[bool] = None) -> Optional[bool]:
    v = config.get(key)
    if v is None:
        return default
    v2 = v.strip().lower()
    if v2 in ("1", "true", "yes", "y", "on"):
        return True
    if v2 in ("0", "false", "no", "n", "off"):
        return False
    raise ValueError(f"Env {key} should be boolean-like, got: {v!r}")

def getenv_list(key: str, sep: str = ",", strip: bool = True) -> list[str]:
    v = config.get(key, "")
    items = v.split(sep) if v else []
    return [i.strip() for i in items] if strip else items


# ---- 路徑處理 ----
def path(
    key: str,
    base: Optional[Path] = None,
    must_exist: bool = False,
) -> Path:
    """
    將 env[key] 解析為 Path：
    - 絕對路徑：直接回傳
    - 相對路徑：視為相對於 base（預設 CONFIG_DIR）
    """
    val = require(key)
    p = Path(val)
    base_dir = base or _CONFIG_DIR
    resolved = p if p.is_absolute() else (base_dir / p)
    resolved = resolved.resolve()
    if must_exist and not resolved.exists():
        raise FileNotFoundError(f"{key} path not found: {resolved}")
    return resolved


# ---- 小工具 ----
def group(prefix: str) -> dict[str, str]:
    """以前綴篩選成子 dict（大小寫完全比對）。"""
    return {k: v for k, v in config.items() if k.startswith(prefix)}


# ---- 方便 REPL 檢視 ----
if __name__ == "__main__":
    # 不印出任何敏感值，只列出有幾個 key 與部分示範
    print(f"[config] total keys: {len(config)}")
    print("APP_ENV:", getenv("APP_ENV"))
    print("CONFIG_DIR:", _CONFIG_DIR)
