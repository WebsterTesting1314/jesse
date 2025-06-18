 # Project Overview

 本文档对项目结构、关键组件和技术栈做简要概览，帮助开发者快速了解仓库布局。

 ## 1. 目录结构概览
 ```
 .
 ├── .cursor
 ├── .env.example
 ├── .gitignore
 ├── contracts/          # Solidity 合约及 OpenZeppelin 文档
 ├── core/               # 核心系统设计与部署指南
 ├── strategies/         # Python 策略脚本
 ├── package.json        # Node 依赖声明
 ├── package-lock.json
 ├── README.md           # 项目主文档
 └── 其他杂项文件
 ```

 ## 2. 关键模块概览
 - **contracts/**：所有 Solidity 合约源码、生成输出 (out/) 及 OpenZeppelin 文档
 - **core/**：系统设计、部署指南等核心文档
 - **strategies/**：Python 量化策略实现
 - **文档**：AsciiDoc 格式的 OpenZeppelin 文档位于 contracts/lib/openzeppelin-contracts/docs/

 ## 3. 开发 & 构建
 - Python：策略脚本基于 Jesse 框架 (strategies/DeFiArbitrageStrategy.py)
 - Solidity：合约在 Foundry/Hardhat 下编译，输出位置 contracts/out/
 - 文档：使用 AsciiDoc (Antora) 构建 OpenZeppelin 文档
 - 部署：详见 DEPLOYMENT_GUIDE.md

 ## 4. 接下来
项目仍然缺少静态分析、测试用例与 CI/CD 流程，可参考项目根目录下的 .pre-commit-config.yaml、.github/workflows/ci.yml 以及 `CONTRIBUTING.md` 中的一键检查脚本和本地/CI 演练指南。
 