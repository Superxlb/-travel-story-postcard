# HTML 填充说明

仅在生成成品时读取。源模板允许 `{{变量}}`，最终 HTML 不得残留。模板不是示例成品；`demo/example-postcard.html` 和 `demo/editorial-postcard.html` 是两种结构的已完成演示作品。

## 布局可以自由设计

先按 [布局设计指南](layout-design.md) 决定结构，在本次输出目录写一个新的 HTML/CSS 模板，再用 `--template 本次设计.html` 指定。可以从空文件创作，也可改编现有模板；脚本只保证内容安全填充，不负责自动选版式或读图。`assets/postcard-template.html` 是省略该参数时的保底样式，不是唯一设计。

模板须包含下表全部变量，可改变任意结构与样式，也可重复放置同一变量。模板由智能体本地创作、审阅，不把用户正文作为模板代码；模板自身的离线性和响应式效果需要单独检查。

```sh
python scripts/render_postcard.py --data demo/example-content.json --image demo/sample.jpg --template demo/editorial-template.html --output outputs/new-layout.html
```

## 推荐：运行本地脚本

运行依赖只有 Python 3.8+ 标准库。不需要 API key、pip 安装或联网。脚本只负责填充，不读懂照片，也不生成故事；先由宿主完成读图和创作。

在 Skill 根目录执行：

```sh
python scripts/render_postcard.py --data demo/example-content.json --image demo/sample.jpg --output demo/my-postcard.html
```

输出必须是新文件；不覆盖已存在成品或原图。默认原图字节嵌入单文件，不做滤镜、裁切或压缩。图片只做格式签名检查，能否正常解码仍需浏览器验证。若需节省 HTML 大小，加 `--image-mode relative`，同时交付生成的 HTML 和旁边的 `*-photo.jpg`（或对应扩展名）。这会复制图片而不改源文件；不支持 SVG 等可含主动内容的格式。

只有描述时可用 `--description-only` 替代 `--image`，成品明确显示“未附照片”，不会借用演示照片。

## 内容 JSON

字段值均为字符串。必填 `title`、`caption`、`recipient`、`story`、`wish`、`photo_alt`。故事用两个换行分段。可选 `location`、`date`、`signature`、`credit`：省略或空串就不显示，日期按用户提供文本，不自动取今天。`photo_alt` 只描述可靠画面；`credit` 用于演示照片来源或用户要求的说明，不放入正文。

以上是文案字段。另可添加结构化 `photo` 对象，控制不透明度、适配、对齐、框比例、衬底色和圆角，详见 [照片调整说明](photo-adjustments.md)。脚本仅接受规定的枚举、数值和颜色，不接受用户原始 CSS。`PHOTO_HTML` 会包含照片框及 img，而不总是单独一个 img。

实际可运行输入见 [example-content.json](../demo/example-content.json)。用户图片与私人 JSON 放在仓库之外的输出目录，避免进入公开仓库。

## 模板变量和手工替换

| 变量 | 含义与安全填充方式 |
| --- | --- |
| TITLE | 标题，同时用于浏览器标签页；HTML 文本转义 |
| CAPTION | 照片短句；HTML 文本转义 |
| RECIPIENT | 收件人；HTML 文本转义 |
| WISH | 寄语；HTML 文本转义 |
| PHOTO_HTML | 只由受信任程序构造 img 标签，src 是校验后的图片 data URI 或安全的相对图片路径，alt 转义；无图时为明确说明块 |
| STORY_HTML | 每段先转义，再由程序包裹 p；段内换行可变成 br |
| META_HTML | 仅对非空地点、日期、署名转义，再用 br 分隔 |
| CREDIT | 普通来源说明文本，转义；不插入可执行链接 |

手工生成也必须转义 `& < > " '`；不能把用户提供的 HTML、URL 或 CSS 直接插入结构变量。脚本额外编码花括号，让用户原文中的模板样式字符串保留显示但不触发替换。一次性替换模板源上的占位符，不递归替换用户文本。

## 排版与交付

保底模板采用奶白 `#fff9ee`、深蓝灰 `#283e45`、陶土 `#92543e`，是推荐配色，不是照片采样。新设计可另选配色与结构，写入受信任的本次模板后再生成新文件。照片保留全幅，可使用自然宽高或 contain，不拉伸主体。正文不设会截断内容的固定高度或隐藏溢出。

打开成品检查照片、中文、桌面/手机宽度与打印预览。打印是普通浏览器 A4 排版，不代表专业明信片印刷标准；长文可能跨页，需检查分页。不支持预览时如实说明只完成静态检查。浏览器无需联网，模型创作本身是否可离线由宿主决定。
