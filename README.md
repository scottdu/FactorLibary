# FactorLibary
## 因子库构建( •̀ ω •́ )y
1. 整体流程（To Do）：

2. Bug修复情况：
### 2017-04-16 修复千分位归一化bug，因为mmt,Yield计算跟其他方式不一样，他们依赖于前一个月或后一个收盘价
所以可能出现总数不一样的情况，此时分母应该为该因子的所有排名值（注意因子数值若相同，排名值应该相同）