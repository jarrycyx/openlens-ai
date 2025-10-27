---
name: chinese_reminders
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
- 中文
- Chinese
- 中国
- 汉语
- 华语
- 汉字
---



### 🧠 Micro-Agent 提示脚本：中文字体与 LaTeX 支持

When generating Python code using Matplotlib or LaTeX, ensure full Chinese character compatibility.

## Matplotlib 中文字体设置
If the user wants to display Chinese characters in Matplotlib plots:
- Always import matplotlib and set the font to a Chinese-compatible one (e.g., SimHei or Microsoft YaHei).
- Ensure minus signs are displayed correctly.

Example:
```python
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体
plt.rcParams['axes.unicode_minus'] = False    # 正常显示负号
plt.title("中文标题示例")
plt.xlabel("横轴")
plt.ylabel("纵轴")
plt.show()
````

If running in a Linux or server environment, check available fonts with:

```python
from matplotlib.font_manager import fontManager
print([f.name for f in fontManager.ttflist])
```

and select a font that supports Chinese, such as `"Noto Sans CJK"` or `"AR PL UMing CN"`.

## LaTeX 中文支持

* Use XeLaTeX or LuaLaTeX with CJK or xeCJK packages.
* Avoid pdflatex for Chinese text.
* Include this LaTeX preamble:

```latex
\usepackage{xeCJK}
\setCJKmainfont{SimSun} % or another available Chinese font
```

* Use UTF-8 encoding in all source files.
