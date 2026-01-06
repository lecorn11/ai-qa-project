from langchain_core.tools import tool

@tool
def calculator(expression: str) -> str:
    """
    计算数学表达式

    输入应该是一个有效的 Python 数学表达式，如'2 + 3 * 4'、'100 / 5'、'2 ** 10'。
    支持加减乘除、幂运算、括号等
    """
    try:
        # 安全检查：只允许数字相关字符
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in expression):
            return "错误：表达式包含不允许的字符"
        
        result = eval(expression)
        return str(result)
    except ZeroDivisionError:
        return "错误：除数不能为零"
    except Exception as e:
        return f"计算错误：{e}"