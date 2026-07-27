# 🧰 工具箱 for 数据处理

Mia 自用 + 团队共享的数据处理小工具集。全部纯前端，数据不出本地浏览器。

## 📦 收录工具

| # | 工具 | 说明 |
|---|---|---|
| 01 | 随机抽样 | 从表格/文本中按数量或比例随机抽样 |
| 02 | 表格数据去重 | 上传 Excel/CSV，按列去重导出 |
| 03 | URL encode/decode | URL 编码解码，支持批量 |
| 04 | 长表格查看器 | 大数据表格分页/搜索/筛选查看 |

## 🚀 使用方式

**方式一：在线（推荐）**
直接访问部署好的 URL（部署完后填写）。

**方式二：本地**
1. 下载整个仓库
2. 双击 `index.html`

## 🔒 数据安全

- 所有工具在浏览器本地运行，数据不发送到任何服务器
- 可断网使用，可用浏览器 Network 面板自行验证
- 部分工具使用 jsDelivr CDN 加载解析库（xlsx.js），仅加载库文件

## 📁 目录结构

```
mia-toolbox/
├── index.html                                    # 门户首页
├── README.md
└── tools/
    ├── 01-random-sampler/random-sampler.html
    ├── 02-dedup/dedup.html
    ├── 03-url-codec/url-codec.html
    └── 04-table-viewer/table-viewer.html
```

## 🛠 部署到 EdgeOne Pages

1. 把本仓库推到 GitHub / Gitee / 腾讯工蜂
2. 登录 [EdgeOne 控制台](https://console.cloud.tencent.com/edgeone/pages)
3. 新建项目 → 授权 Git → 选中本仓库
4. 构建配置：**无需构建**（纯静态），输出目录 `/`
5. 部署完成后获得 `xxx.edgeone.app` 的 URL
6. 之后 `git push` 会自动触发重新部署

## 📝 更新日志

见门户右上角"📝 工具箱更新日志"按钮。

## 🤝 反馈

有 bug、想加新工具、或有优化建议，直接找 Mia。
