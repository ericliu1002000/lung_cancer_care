# 医生端-报告详情指标异常联动标色设计

## 背景

医生端患者报告详情页中的复查指标面板，当前已经完成“查看指标分析数据”接口对接，前端可正常展示以下列：

- 编码
- 中文名
- 结果
- 单位
- 参考区间
- 上次结果
- 与上次变化

现状问题是：

- `结果` 列只做了文字颜色区分，没有单元格底色高亮
- `编码`、`中文名`、`上次结果`、`与上次变化` 没有按当前异常结果做统一联动标色
- `与上次变化` 仍沿用“上升/下降”自己的颜色语义，与本次异常高低展示规则不一致

这导致医生在浏览复查指标时，需要逐列扫描文字颜色，不利于快速识别异常项，也与目标参考样式不一致。

## 目标

- 在 `templates/web_doctor/partials/reports_history/_record_detail.html` 的复查指标表格中增加异常联动底色高亮
- 当当前结果高于正常区间时，让以下列统一显示红色异常态：
  - 编码
  - 中文名
  - 结果
  - 上次结果
  - 与上次变化
- 当当前结果低于正常区间时，让同一批列统一显示蓝色异常态
- 当当前结果正常或无异常标识时，保持现有中性样式
- 当 `上次结果` 或 `与上次变化` 的值为 `-` 时，这两个单元格保持中性，不参与联动标色
- 保持当前接口结构基本不变，以前端展示层改造为主

## 非目标

- 不改动指标面板的字段顺序
- 不调整“单位”“参考区间”两列的样式语义
- 不新增指标编辑能力
- 不把本次联动标色规则下沉为后端必须输出的新展示字段
- 不改造接口分页、缓存、面板展开收起逻辑
- 不在本次需求中改变表格整体布局和容器结构

## 已确认规则

### 当前结果异常方向

- `abnormal_flag == 'HIGH'`：当前结果高于正常区间
- `abnormal_flag == 'LOW'`：当前结果低于正常区间
- 其它情况：视为正常或中性

### 联动标色范围

固定联动 5 列：

- `field_code`
- `field_name`
- `current_value_display`
- `previous_value_display`
- `delta_display`

不参与联动的中性列：

- `unit`
- `reference_range`

### 联动标色规则

- 当当前结果为 `HIGH` 时：
  - `编码`、`中文名`、`结果` 必定红底
  - `上次结果`、`与上次变化` 若不为 `-`，也显示红底
- 当当前结果为 `LOW` 时：
  - `编码`、`中文名`、`结果` 必定蓝底
  - `上次结果`、`与上次变化` 若不为 `-`，也显示蓝底
- 当当前结果正常时：
  - 上述 5 列都保持默认中性样式
- 当 `previous_value_display == '-'` 时：
  - `上次结果` 单元格保持中性
- 当 `delta_display == '-'` 时：
  - `与上次变化` 单元格保持中性

### 与上次变化列的语义调整

当前模板中 `与上次变化` 通过 `delta_direction` 使用“上升绿、下降红、无变化灰”的配色。

本次需求确认后，`与上次变化` 的颜色规则调整为：

- 不再根据 `delta_direction` 决定颜色
- 完全跟随当前结果的 `abnormal_flag`
- 仅当 `delta_display != '-'` 时才参与联动底色

`delta_direction` 仍可保留在接口数据中，供后续其它功能使用，但本次 UI 不再依赖它做着色判断。

## 方案对比

### 方案 A：模板内直接写联动 `:class`

做法：

- 在 `_record_detail.html` 的每个目标单元格上直接写 `:class`
- 通过 `row.abnormal_flag`、`row.previous_value_display`、`row.delta_display` 做条件判断

优点：

- 改动面最小
- 实现速度最快

缺点：

- 模板判断会明显增多
- 样式语义分散，不利于后续维护
- 同一规则会在多个 `td` 中重复

### 方案 B：在 Alpine 状态中封装样式助手方法

做法：

- 在 `static/web_doctor/reports_history.js` 的 `buildConsultationReportDetailState()` 中新增样式助手方法
- 模板只负责调用方法，不直接承载复杂判断

优点：

- 规则集中，模板更清晰
- 后续改配色或联动范围时只需改一处
- 与当前 HTMX partial + 全局工厂函数模式兼容

缺点：

- 比纯模板方案多一层方法封装

### 方案 C：后端接口新增展示态字段

做法：

- 在 `health_data/services/checkup_results.py` 中新增如 `highlight_level`、`previous_should_highlight`、`delta_should_highlight` 等字段
- 前端只消费这些字段渲染

优点：

- 前后端语义边界更明确
- 模板和 JS 更轻

缺点：

- 为展示逻辑扩充 payload，性价比不高
- 需要额外补接口测试与兼容处理

### 结论

采用方案 B。

原因：

- 当前接口已返回 `abnormal_flag`、`previous_value_display`、`delta_display`，足够支撑联动规则
- 这次变更本质是展示规则升级，不是数据模型升级
- 将规则收敛在 `buildConsultationReportDetailState()` 中，比把判断散落在模板内更稳定

## 页面与交互设计

### 作用区域

仅作用于报告详情中的复查指标面板表格，即：

- 面板容器保持不变
- 表头结构保持不变
- 仅调整表格 `tbody` 里的异常列着色

### 颜色语义

推荐使用浅色底 + 深色字，避免纯色大面积铺满导致阅读疲劳。

建议映射如下：

- `HIGH`：
  - 背景：浅红
  - 文字：深红
- `LOW`：
  - 背景：浅蓝
  - 文字：深蓝
- `NORMAL`：
  - 背景：白色或默认背景
  - 文字：现有灰黑色

实现时优先复用 Tailwind 内置类，不新增自定义 CSS。

### 单元格行为

#### 编码、中文名、结果

- 直接跟随当前结果异常方向
- 不需要额外判断是否为 `-`

#### 上次结果

- 当 `previous_value_display != '-'` 时：
  - 跟随当前结果异常方向联动标色
- 当 `previous_value_display == '-'` 时：
  - 保持中性样式

#### 与上次变化

- 当 `delta_display != '-'` 时：
  - 跟随当前结果异常方向联动标色
- 当 `delta_display == '-'` 时：
  - 保持中性样式

#### 单位、参考区间

- 始终保持中性样式
- 不参与异常联动

## 前端设计

### 模板层职责

变更文件：

- `templates/web_doctor/partials/reports_history/_record_detail.html`

模板层职责限定为：

- 为目标 `td` 绑定统一样式方法
- 对 `previous_value_display`、`delta_display` 是否为 `-` 做最小化条件调用
- 保持当前 `x-for`、`x-show`、`x-text` 结构不变

模板层不负责：

- 内联定义整套异常等级映射
- 维护复杂颜色类拼接逻辑

### Alpine 状态职责

变更文件：

- `static/web_doctor/reports_history.js`

在 `window.buildConsultationReportDetailState = function (config) { ... }` 中新增样式助手方法，建议职责拆分为：

1. 解析当前行异常级别
2. 返回异常单元格 class
3. 返回中性单元格 class
4. 为“可空值联动字段”提供统一入口

建议的方法形态如下：

- `getMetricAbnormalLevel(row)`
- `getMetricHighlightClass(row)`
- `getMetricCellClass(row, options)`

方法职责说明：

- `getMetricAbnormalLevel(row)`
  - 输入：单行 `row`
  - 输出：`high | low | normal`
- `getMetricHighlightClass(row)`
  - 输入：单行 `row`
  - 输出：该行异常联动样式类字符串
- `getMetricCellClass(row, options)`
  - 输入：
    - `row`
    - `options.allowPlaceholderNeutral`
    - `options.value`
  - 输出：最终绑定到 `td` 的类字符串
  - 用于兼容 `上次结果` / `与上次变化` 在值为 `-` 时回退到中性样式

本次实现中，函数方法需补充完整中文注释，说明入参和返回值。

### 推荐样式映射

为避免类名在模板中重复散落，建议 JS 中集中返回如下 Tailwind 类组合：

- `HIGH`：
  - `bg-rose-100 text-rose-700`
- `LOW`：
  - `bg-sky-100 text-sky-700`
- `NORMAL`：
  - `text-slate-700` 或现有默认色

如果需要兼顾表格分隔线可读性，可在异常态保留现有 `px-2 py-1.5` 不变，仅附加颜色类。

## 后端设计

### 接口保持不变

当前接口：

- `web_doctor:patient_report_image_metrics`

当前由 `build_report_image_metrics_payload(report_image)` 组装行数据，已输出：

- `field_code`
- `field_name`
- `current_value_display`
- `unit`
- `reference_range`
- `previous_value_display`
- `delta_display`
- `delta_direction`
- `abnormal_flag`

本次设计不要求新增字段，因为前端联动规则可直接基于：

- `abnormal_flag`
- `previous_value_display`
- `delta_display`

完成判断。

### 不下沉展示字段的原因

- 当前逻辑没有新的业务判断依赖后端数据推导
- 若把联动样式判断拆到接口，会让展示细节和业务 payload 绑定过深
- 当前需求更适合作为组件展示层规则实现

## 数据流

1. 用户点击“查看指标数据”按钮。
2. 前端通过现有 `toggleMetricPanel(imageKey, metricsUrl)` 拉取或读取缓存的指标数据。
3. 接口返回当前图片对应的指标 payload。
4. `activeMetricData.rows` 驱动表格渲染。
5. 模板对每一行调用 Alpine 样式助手方法。
6. 样式助手基于 `row.abnormal_flag` 决定联动颜色。
7. 当 `previous_value_display` 或 `delta_display` 为 `-` 时，对应单元格回退为中性样式。

## 测试设计

### 前端模板渲染验证重点

至少覆盖以下展示规则：

1. `HIGH` 行时，`编码`、`中文名`、`结果` 显示红色异常态
2. `HIGH` 行且 `previous_value_display != '-'` 时，`上次结果` 也显示红色异常态
3. `HIGH` 行且 `delta_display != '-'` 时，`与上次变化` 也显示红色异常态
4. `LOW` 行时，上述联动列显示蓝色异常态
5. `previous_value_display == '-'` 时，该格不显示红蓝异常态
6. `delta_display == '-'` 时，该格不显示红蓝异常态
7. 正常行保持中性样式
8. `单位` 与 `参考区间` 始终保持中性样式

### 自动化测试建议

本次需求主要改动前端模板与 Alpine 样式映射，后端 payload 结构不变，因此测试优先级建议为：

- 第一优先级：补充模板输出断言或页面响应内容断言，确保新类名被正确渲染
- 第二优先级：如当前测试体系不便覆盖 Alpine 动态 class，则至少补充接口和模板存在性相关测试，避免回归

如需补足更高置信度，推荐采用以下其一：

- 在 `web_doctor/tests/test_consultation_records.py` 中增加详情模板输出断言
- 或者提取前端样式映射函数做更易验证的单元测试

### 手工验收要点

- 打开任一包含复查指标的图片明细
- 验证高于区间的行是否呈现红底联动
- 验证低于区间的行是否呈现蓝底联动
- 验证 `-` 占位值不会被误标色
- 验证指标面板展开、收起、缓存读取行为未受影响

## 风险与取舍

### 风险 1：模板中内联判断过多，后续难维护

如果把所有条件都直接写在模板里，会导致 `_record_detail.html` 可读性下降。

结论：

- 把异常联动规则集中在 `reports_history.js`
- 模板只保留最小绑定

### 风险 2：继续沿用 `delta_direction` 旧语义，造成双色规则冲突

如果“与上次变化”仍按上升/下降配绿红，而其它列按高低异常配红蓝，会让同一行出现两套颜色语言。

结论：

- 本次放弃 `delta_direction` 的着色职责
- 统一跟随当前结果异常方向

### 风险 3：占位值 `-` 参与联动导致误导

如果 `上次结果` 或 `与上次变化` 没有实际值却仍然高亮，会让医生误以为有真实历史数据。

结论：

- 占位值 `-` 必须保持中性

## 影响范围

预计变更文件：

- `templates/web_doctor/partials/reports_history/_record_detail.html`
- `static/web_doctor/reports_history.js`
- `web_doctor/tests/test_consultation_records.py` 或同模块相关测试文件

不涉及变更：

- `patient_report_image_metrics` 路由
- `web_doctor/views/reports_history_data.py` 接口逻辑
- `health_data/services/checkup_results.py` payload 结构

## 待实现清单

- 在 Alpine 状态中新增指标异常联动样式助手方法
- 更新 `_record_detail.html` 中目标列的动态 class 绑定
- 移除 `与上次变化` 对 `delta_direction` 着色的依赖
- 补充最小必要测试，覆盖高低异常和占位值不标色场景
- 验证现有指标面板缓存与展开行为不回归

## 最终结论

本次功能采用“前端 Alpine 统一样式映射 + 模板轻绑定”的方案。

该方案在不扩张后端接口职责的前提下，完成复查指标表格的异常联动标色升级。当前结果高于区间时，目标列统一呈现红色异常态；低于区间时统一呈现蓝色异常态；占位值 `-` 保持中性。这样既满足医生快速识别异常项的诉求，也能保持当前 HTMX partial 与 Alpine 组件结构的稳定性。
