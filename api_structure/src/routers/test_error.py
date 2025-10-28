from src.handlers.abort_examples import example_abort
from src.handlers.warning_examples import example_warning
from core.timer import timed
from core.logger import set_extract_log

@timed(task_name="test_endpoint")
async def test_endpoint(input_text: str) -> dict:
    # 1/0  # 控制模擬 錯誤 非預期錯誤
    abort_result = await example_abort(input_text)
    abort_result_ = await example_warning(abort_result)
    warning_result = await example_warning(abort_result_)

    set_extract_log({
            "extra_info": "Test error handling endpoint",
            "log": "這個我都亂寫的 依照專案調整唷",
        })
    
    return {
        "abort_result": abort_result,
        "warning_result": warning_result
    }