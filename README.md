# auto-zhipin

通过[Playwright](https://github.com/microsoft/playwright-python)自动拉取Boss直聘的岗位信息，并结合求职者的简历进行智能匹配。利用大模型筛选出最契合求职者背景与需求的优质岗位，从而高效提升求职成功率。

## 安装

**1.** 拉取源码

```bash
git clone https://github.com/ufownl/auto-zhipin
```

**2.** 安装依赖项

```bash
cd auto-zhipin
uv sync
uv run playwright install
```

**3.** 参考[文档](https://fast-agent.ai/ref/config_file/)配置API\_KEY

```
# fastagent.secrets.yaml

googleoai:
  api_key: "$YOUR_GEMINI_API_KEY"
```

## 使用

目前暂时只实现了命令行查询工具，用法如下:

```bash
$ uv run query.py --help
usage: query.py [-h] --resume RESUME [-q QUERY] [--city CITY] [-n SCROLL_N] [--ratings RATINGS] [-O OUTPUT]

查询匹配的职位。

options:
  -h, --help            show this help message and exit
  --resume RESUME       简历文件路径 (目前只支持文本文件，推荐使用Markdown)
  -q, --query QUERY     查询关键字
  --city CITY           BOSS直聘城市代码 (默认: 100010000)
  -n, --scroll_n SCROLL_N
                        最大滚动次数 (默认: 8)
  --ratings RATINGS     可接受的岗位评级 (默认: EXCELLENT,GOOD)
  -O, --output OUTPUT   输出文件路径 (默认: favor_jobs.json)
```

## 声明

本项目仅用于学习用途，尝试使用时请遵守相关法律法规及平台用户协议，否则后果自负。

## License

BSD-3-Clause license. See [LICENSE](https://github.com/ufownl/auto-zhipin?tab=BSD-3-Clause-1-ov-file)
