# 正面、背面与总览 PNG

用户需要的是可直接查看和转发的明信片图片。HTML 用于后续修改；PNG 固定本次渲染的像素与排版，换设备打开不会重新流式排版，但查看器仍可能缩放或压缩图片。

## 默认交付

同一份最终 HTML 生成三张 PNG：

- `postcard-front.png`：完整正面，包含原照片、标题和短句，不是只复制原始 JPG。
- `postcard-back.png`：完整背面，包含收件人、故事、寄语与已提供的落款。
- `postcard-overview.png`：正反面总览，方便快速检查整套作品。

在回复里实际展示正面和背面图片，再附 PNG 下载位置及 HTML 链接。使用宿主支持的图片附件/预览机制；本地 Markdown 图片若受支持，应引用实际绝对路径。只列 HTML 路径不算完成图片交付。

只有截图成功且经过查看才能称“已导出图片”。浏览器截图不可用时仍交付 HTML 和文案，明确说明 PNG 未生成，不能把 HTML 改名成 PNG 或把原照片当排版成品。

## 截图步骤与结构约定

1. 完成并保存最终 HTML，先检查布局。透明度、裁切、圆角等显示效果也应已写入这一版本。
2. 给完整正面容器添加 `data-postcard-side="front"`，完整背面容器添加 `data-postcard-side="back"`。也兼容已有的 `aria-label="明信片正面"` 与 `aria-label="明信片背面"`。
3. 用唯一的 `main` 包裹正反面；若用 `data-postcard-overview`，将属性加在同一个 main 上，不要另建一个会重复匹配的容器。这些标记不限制布局结构。
4. 优先使用宿主现有浏览器截图工具；固定选定的视口，等待中文字体与所有图片加载完毕，再分别截取整个正面、背面及总览元素。不能只截屏幕当前可见部分而遗漏下方正文。
5. 默认桌面视口宽 1440 CSS 像素、输出倍率 2。可以根据设计调整；这只是像素清晰度，不代表 300 DPI 或专业印刷规格。导出每一面时保留选定视口的样式，不为单面截图重新套版。
6. 查看导出的正面、背面，确认中文正常、照片可见、主体与文字没有新增截断。截图只会固定当前画面，不能修复本来错误的排版；发现问题就修 HTML 后重新导出。
7. 后续修改文案、排版或照片显示时，同时重新生成三张图片，使用新文件名或新目录，避免把旧截图当新结果。

## 可选自动导出脚本

依赖：Node.js 20+、Playwright，以及本地可启动的 Chromium / Chrome / Edge（Node 下限依据本次已安装 Playwright 的 engines 字段）。与只依赖 Python 标准库的 HTML 渲染脚本分开。优先使用已有依赖与宿主工具；没有时说明依赖，遵循宿主权限规则，不声称安装 Skill 已自动安装浏览器。

如果用户自行准备独立工具目录，可在该目录安装：

```sh
npm install playwright
npx playwright install chromium
```

让运行脚本的 Node 能解析该目录下的 playwright，例如使用当前环境支持的模块搜索路径。已有 Chrome/Edge 时可用 `--browser` 指向真实可执行文件；不需要再下载 Chromium，也不要猜用户路径。包内不硬编码开发机器路径。

在 Skill 根目录执行：

```sh
node scripts/export_postcard.cjs --html demo/photo-adjusted-postcard.html --output-dir outputs/png --prefix postcard
```

默认导出三张 PNG 与一份 `postcard-export.json`，后者记录来源 HTML 的 SHA-256、视口、像素倍率、浏览器版本和图片尺寸，便于确认对应同一版。元数据不需要出现在明信片正文。

自定义例子：

```sh
node scripts/export_postcard.cjs --html 成品.html --output-dir 新导出目录 --prefix 明信片 --width 1440 --scale 2 --browser 实际浏览器路径
```

脚本只读取本地 HTML，阻止外部 HTTP 资源、禁用页面脚本，等待字体和图像解码；正背面标记缺失、重复、图片损坏、内容溢出时拒绝导出。输出不覆盖旧文件。它导出的是完整明信片页面区域，不修改原照片字节。不要对来源不明的任意网页执行本工作流。
