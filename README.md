> Why don't you say that three times, 'Within cells interlinked'?
> 
> Within cells interlinked.
> 
> Within cells interlinked.
> 
> Within cells interlinked.

# Cellink 引擎简介

Cellink 引擎是驱动“责任链模式”（Chain of Responsibility Pattern）编程的一套代码（以下简称 Cellink）。责任链模式编程具有诸多优势，其中最突出的，是实现各模块间的解耦。关于责任链模式编程互联网上有很多内容，这有篇很棒的博客可供参考：[责任链模式](https://www.runoob.com/design-pattern/chain-of-responsibility-pattern.html) 。



## 设计动机

**人是视觉动物。** 健康人类 80% 的日常活动都依赖视觉（在开发者的工作中比重可能会更高）。Cellink 允许可视化你的项目。无需另行维护，Cellink 能绘制各任务模块间的关系。让我试举例说明情况。以下流程图来自我的三个项目，它们都用 Cellink 管理：

项目一：
![](assets/imgs/adc-graph.png)

项目二:
![](assets/imgs/bearing-graph.png)

项目三:
![](assets/imgs/nozzle-graph.png)

以计算机工业视觉领域为例，来阐述 Cellink 的使用场景。一般来说，计算机视觉项目由多个子模块构成（很多其它项目亦如此），其中有些负责数据解析和格式化，有些负责图像预处理，另一些则负责算法推断。

很多业务场景要求把原始图像分割成多个 ROI 区域，每个区域做单独处理。比如手机的外观检测，某个业务模块只关注充电口附近的缺陷。需要先把充电口附近的区域提取出来，作预处理以后，再传给特定算法模块检测。

通常会差分成如下步骤：1) 载入原始手机图片，2) 定位手机所在的图像区域，3) 在此基础上继续分割出充电口附近的像素，4) 算法模块执行检测任务。

以上的每个步骤都能抽象成“节点”（有关“节点”的更多细节，我们会在后面章节介绍），每个节点执行后会产生相应的数据传给下一个节点执行。

这套以节点来封装工作任务的范式，就是“责任链模式”编程的内涵。

Cellink 提供了一套简单的机制来管理各节点的流向，确保正确的执行次序。更重要的是，Cellink 能绘制各节点的关系图（如上所示），让开发者看清楚自己所开发的任务模块在项目中的位置。这种空间上的知觉让我在项目实践中获得了极大的把控感。哪怕面对历史久远的项目，也不会在代码的迷雾中迷失。



### 工作原理

Cellink 通过搭建“有向无环图”（DAG）对项目流程进行建模。任务模块是有向无环图的节点。所有节点都能直接访问父节点的内容。

Cellink 支持几种简单的图操作（比如遍历，广播，和路径搜索等等），可以覆盖各种业务需求。



### Cellink 的局限

编写开发文档、维护项目流程图是优秀程序员的必备技能。在某些中大型项目中，项目流程在架构设计阶段就已明确，因此 Cellink 的绘图功能似乎显得多余。但 Cellink 流程图由项目代码生成，真实反映了当前代码的运行逻辑。一方面能可视化开发进度，另一方面，也能协助开发者发现代码与设计流程图冲突之处。

截止目前（2022年9月），Cellink 只在我们团队有限的实践中发挥了作用，而这些项目的规模都不大。我们尚不清楚它是否能被有效推广到大型、或某些特殊的项目中（比如有很多并行需求的程序）。

此外， Cellink 还受编程语言的限制。因为极端依赖 Python 的某些特性（比如装饰器），目前 Cellink 只支持用 Python 开发的项目。但我们期待后续能在更多编程语言上取得突破。



## 基本概念介绍

### 一、节点

“节点”是 Cellink 的基本类型。为了简单起见，我们没设计其它类型。因此，**节点类型是 Cellink 里的唯一类型**。Cellink 的所有功能，都通过节点的方法实现。

根据不同的输入类型，Cellink 提供了 5 种节点的基类：

```python
class NodeSI # 单输入节点（Single Input）
class NodeMI # 多输入节点（Multiple Inputs）
class NodeCI # 条件輸入节点（Conditional Inputs）
class NodeNI # 非门节点（NOT Gate Inputs）
class NodePI # 特殊的单输入节点（Special Single Inputs）
```


下图是这 5 种节点的可视化结构展示：

![三种节点结构](assets/imgs/node-types.png)

- **NodeSI**：只有一个父节点
- **NodeMI**：挂载一个或多个父节点
- **NodeCI**：和 NodeMI 类似，挂载多个父节点。区别在于，执行 NodeMI 的条件是所有父节点都能执行；而 NodeCI 只要任一父节点能执行就行
- **NodeNI**：只挂载一个父节点，父节点被访问且不能执行（forward 方法返回 False） 的时候才被执行
- **NodePI**：一种特殊的 NodeSI 节点。功能和挂载方式跟 NodeSI 完全一样，差别在于显示。当一个节点挂载了多个 NodeSI 子节点时，图结构会往横向拓展，导致图变得很宽很难看。如果替换成 NodePI 节点，它们会被收集起来往纵向排列，让图变苗条，增加美感与可读性



#### 创建节点

Cellink 通过继承节点类来创建新节点。下代码展示如何创建一个 NodeSI 节点：

```python
from cellink import NodeMI

class Diff(NodeMI):
    def __str__(self):
        return 'diff'
```



#### 访问父节点

子节点可以通过类变量来访问父节点：

- **parent**：NodeSI 和 NodeNI 类型的父节点
- **parent_list**：NodeMI 和 NodeCI 类型的父节点列表（之所以不叫 parents 是怕拼写上容易与 parent 混淆）

父节点列表 parent_list 还有以下两点特性：

1. 父节点在 parent_list 中的次序与被挂载时的次序相同。有关父节点的挂载，下个章节会介绍
2. 如果 NodeCI 的某个父节点无法执行，那么对应 parent_list 元素的值为 None



#### 根节点

没有任何父节点的节点叫根节点。一个项目里可以有多个根节点。

根节点可选择继承 NodeSI/NodeMI/NodeCI 中的任何一个，Cellink 不做限制。

根节点一般是整个项目的数据入口。我们发现，用类方法（@classmethod）实例化根节点是比较好的实践：

```python
class Root(NodeSI):
    @classmethod
    def initialize(cls, val):
        root = cls()
        root.val = val
        return root

root = Root.initialize(42)
```



### 二、图

“图”由节点组成。子节点用装饰器 ``@hook_parent`` 挂载父节点。Cellink 的内部机制确保了图的有向无环结构。

下面代码展示了如何用 3 个节点搭建一个简单的图：

```python
from cellink import NodeSI
from cellink import NodeMI
from cellink import hook_parent

class RGB(NodeSI): # 此为根节点（没有父节点），可继承任何节点类型
    @classmethod
    def from_image_path(cls, image_path):
        att = cls()
        att.img = cv2.imread(image_path)
        return att

@hook_parent(RGB)
class Gray(NodeSI):
    def __str__(self):
        return 'gray'

    def forward(self):
        rgb_img = self.parent.img  # 通过 self.parent 访问父节点
        self.img = rgb2gray(rgb_img)
        return True

@hook_parent(RGB, Gray)
class Diff(NodeMI):
    def __str__(self):
        return 'diff'

    def forward(self):
        rgb_img  = self.parent_list[0].img  # 访问父节点 RGB
        gray_img = self.parent_list[1].img  # 访问父节点 Gray
        self.img = np.abs(rgb_img.astype('float32') - gray_img[:,:,None])
        return True
```

上面代码由 Cellink 绘制的流程视图如下：

![](assets/imgs/demo-graph.png)

**当一个节点被实例化时，图中的所有其它节点都会被实例化，于是它所在的图也完成了实例化：**

```python
rgb = RGB() # 此时其它两个节点的实例也会随着被实例化
rgb.draw_graph() # 节点被实例化时，图也跟着被实例化
```



## 创建节点

新节点在创建时需要继承三个节点类（NodeSI/NodeMI/NodeCI）中的一个，并重载以下 3 个方法：

1. **\_\_str\_\_**：创建节点名称。可缺省

2. **forward**：前向处理方法。可缺省

3. **backward**：反向处理方法。可缺省

我们一一展开介绍。



### 1. 节点名称 \_\_str\_\_：

节点的名称通过重载 \_\_str\_\_ 方法定义。如缺省，则以类名代替：

```python
class Rocket(NodeSI):
    def __str__(self):
        return 'rocket'
```

注：发现重名节点 Cellink 会报错。



### 2. 前向处理 forward：

Cellink 能推动从根节点出发，正向传播的业务流。沿途节点的 forward 方法会被依次调用。

forward 方法承载当前节点的业务逻辑。通常需要访问并处理父节点的数据，生成自己的数据。

forward 方法返回一个 boolean 值，通知 Cellink 后台是否执行成功。

forward 方法在缺省时返回 False（根节点返回 True，因为根节点的变量一般在类方法里设置）。

虽然 Cellink 不做限制，我们也不建议开发者在 forward 方法中修改父节点的内容。

Cellink 假定了 forward 方法的业务逻辑很耗时，且在输入数据固定的情况下输出结果不变（没有随机因素）。

**所以 forward 方法在节点的整个生命周期里只执行一次！！！**

**所以 forward 方法在节点的整个生命周期里只执行一次！！！**

**所以 forward 方法在节点的整个生命周期里只执行一次！！！**

这种设计保证了节点中的业务代码不会被重复运行。

以下是 forward 方法的一个示例：

```python
@hook_parent(RGB, Gray)
class Diff(NodeMI):
    def forward(self):
        # 获取父节点的数据
        rgb_img  = self.parent_list[0].img
        gray_img = self.parent_list[1].img
        # 生成自己的数据
        self.img = np.abs(rgb_img.astype('float32') - gray_img[:,:,None])
        # 返回 True 告知后台执行成功
        return True
```



### 3. 反向处理 backward：

Cellink 能推动从当前点出发，反向传播的业务流。沿途节点的 backward 方法会被依次调用。

和 forward 方法一样，backward 方法也返回一个 boolean 值，用于通知 Cellink 后台是否执行成功。

backward 方法缺省时默认返回 False 。

backward 方法比较常见的业务逻辑是对父节点数据进行修改。

backward 方法在机器视觉领域很有帮助。在我们的项目实践中，backward 方法通常用于反向传播检测结果的坐标。因为坐标变换只需在相邻层级的坐标系上进行，极大简化了编程的复杂度。

如果没有将信息反向传播的业务需求，backward 方法可以缺省。

以下是 backward 方法的一个示例：

```python
class ScaleAndTranslate(NodeMI):
    def backward(self):
        scale = self.scale 
        x0, y0 = self.offset
        x, y = self.coordinate
        # 从局部坐标变换到全局坐标
        self.parent.coordinate = (x / scale + x0, y / scale + y0)
        self.parent.classname = self.classname
        return True
```



## 使用 Cellink

Cellink 支持几种简单的图操作（如遍历，广播，和路径搜索等等）。这些操作都通过调用节点中的方法/变量实现。



### 前向搜索 seek：

从所有根节点开始，seek 方法遍历所有到目标节点的前向路径。沿途所有节点的 forward 方法会依次被执行。

seek 方法输入目标节点的名称（该名称通过 \_\_str\_\_ 方法定义），返回目标节点的实例：

```python
diff = rgb.seek('diff')  # 从根节点开始，依次执行沿路各节点的 forward() 方法，并返回 Diff 节点的实例
print(diff.img.shape)  # 因为 diff.forward() 已被执行，diff.img 也被生成
```

如果无法抵达目标节点（沿途的 forward 方法执行失败返回了 False，中断了正向传播的过程），seek 方法返回 None 。

seek 方法可以被任意节点调用，效果是一样的：

```python
node1 = rgb.seek('diff')
node2 = node1.seek('diff')
assert node1 == node2
```



### 反向搜索 retr：

从当前节点出发，retr 方法（retrospect，缩写成四个字母是为了和 seek 等长）遍历所有到目标节点的前向路径。沿途所有节点的 backward 方法会依次被执行：

```python
gray = root.seek('gray')
print(gray.bboxes) # 输出：[[33,100,94,423], [53,16,312,50]]

# 反向传播到根节点
root = gray.retr('rgb')
print(root.bboxes) # 输出某个值
```

如果无法抵达目标节点（沿途的 backward 方法执行失败，中断了反向传播的过程），retr 方法返回 None

retr 方法可以不输入参数，此时 retr 会从当前节点沿路运行所有祖先节点的 backward 方法。此时 retr 方法返回 None：

```python
gray.retr()
print(root.bboxes) # 输出某个值
```



### 索引：\_\_getitem\_\_()

该方法可以索引图中任一节点：

```python
diff = root['diff']
gray = diff['gray']
```

**注意**：和 seek 方法不同，索引操作不触发沿途的 forward 方法。



### 广播：broadcast()

broadcast 方法输入一个字典类型作为信息，并向所有节点广播。其它节点可通过 self.broadcasting （字典类型）读取：

```python
root.broadcast({'greet': 'good morning!'})
print(gray.broadcasting['greet'])  # 输出: good morning!
gray.broadcast({'greet': 'good evening!'})
print(root.broadcasting['greet'])  # 输出: good evening!

# 更直接的广播方法：
root.broadcasting['greet'] = 'good evening!'
print(gray.broadcasting['greet'])  # 输出: good evening!
```

广播机制用于节点间快速通信，类似全局变量。

不建议滥用广播机制。



### 遍历：traverse()

traverse 方法以 callback 函数为输入，该 callback 函数以节点实例为输入，由开发者定义。

traverse 遍历图中所有节点，并对以每个节点为输入执行 callback 函数。最后返回 callback 函数的执行结果列表：

```python
str_node_pairs = diff.traverse(lambda node: (str(node), node)) # 返回 callback 函数的输出列表
str2node = dict(str_node_pairs)
root = str2node['rgb']
```

traverse 方法不触发沿途的 forward/backward 方法。

traverse 方法遍历节点的次序是无规则的。



### 绘制流程视图：draw_graph()

draw_graph 方法绘制流程视图（见上图）。视图保存在工作目录的 ``graph.gv`` 文件中，用 dot 文件查看器可以打开（如 XDot 等）。

```python
root.draw_graph() # 画出整个网络
```



## 装饰器说明

Cellink 定义了两种装饰器：``@hook_parent`` 和 ``@static_initializer`` 。前者用于挂载父节点，后者实现静态初始化功能。



### 挂载装饰器 @hook_parent

@hook_parent 是类装饰器，用于挂载父节点。@hook_parent 以父节点类作输入：

```python
@hook_parent(ParentClass) # 挂载一个父节点
class ChildClass(NodeSI): # 挂载一个父节点时，子节点可继承 NodeSI 类
    def forward(self):
        parent_node = self.parent
        ...

@hook_parent(MotherClass, FatherClass) # 挂载多个父节点
class ChildClass(NodeMI): # 挂载多个父节点时，子节点应该继承 NodeMI 类或 NodeCI 类
    def forward(self):
        mother_node = self.parent_list[0]  # parent_list 的实例类别次序和装饰器输入类别次序一致
        father_node = self.parent_list[1]  # parent_list 第二个元素是 FatherClass 的类实例
        ... 
```



### 静态初始化装饰器 @static_initializer：

@static_initializer 是函数装饰器，用于（静态）加载初始化耗时的内容。设计该装饰器是为了给运行加速 。

让我尝试用案例来说明。很多深度学习项目需要加载 AI 模型，加载模型通常比较耗时。普遍的做法是在初始化阶段一次性完成加载。哪怕某些模型没被用到，却也消耗了加载时间。我们希望 Cellink 能赋予更多灵活性：

1. 只有被 seek 方法触发，相关节点的模型才会被加载

2. 在程序的整个生命周期中，模型不会被重复加载

为了不失一般性，“模型加载”也可以是任何开销昂贵的初始化操作。

以下代码展示了 @static_initializer 的用法

```python
@hook_parent(Image)
class Bump(NodeSI):
    def __str__(self):
        return 'bump'

    @static_initializer
    def initialize_bump_finder(self):  # 该函数在整个进程生涯中只执行一次
        # 加载 AI 模型，耗时操作
        bump_finder = Controller(gpu_id=0)
        return bump_finder

    def forward(self):
        img = self.parent.img
        # 在程序的生命周期中，只有第一次调用会执行该函数的内容，
        # 往后的所有调用只返回第一次调用返回的内容
        bump_finder = self.initialize_bump_finder()
        bump_bboxes = bump_finder(img)

img1 = Image.from_image_path('IMAGE1.JPG')
bump = img1.seek('bump')  # 加载 AI 模型，耗时 2s

img2 = Image.from_image_path('IMAGE1.JPG')
bump = img2.seek('bump')  # AI 模型不会被二次加载，只执行业务代码
```

@static_initializer 装饰器保证被装饰函数在整个进程周期中只调用一次，往后的调用都只是返回第一次加载进来的模型的引用。



## Cellink 实践

本小节介绍几个 Cellink 的编程实践。有些是有意设计的功能，有些是在使用过程中意外发现的特性。

“噢，原来我们可以如此这般 ......”，Cellink 有时会带给创造者惊喜。

我们也希望后来人能挖掘出更多奇妙。



### 实践一：用不同的图实例处理不同的数据

当一个节点被实例化时，它所在图中的所有其它节点都会被实例化。

实例化节点并不会执行业务逻辑，所以哪怕图中有上万个节点，实例化的计算开销也不足一提（相比真正的业务需求）。

前面提到，forward 方法在整个节点的生命周期中只会执行一次，因此节点的输出是固定的。如果要处理不同数据（比如另一张图片），我们建议实例化新的图来处理：

```python
# 实例化一个图，处理第一个数据
rgb1 = RGB.from_image_path('IMAGE1.JPG')
diff1 = rgb1.seek('diff')

# 实例化新图，处理第二个数据
rgb2 = RGB.from_image_path('IMAGE2.JPG')
diff2 = rgb2.seek('diff')
```



### 实践二：大胆托管你的实验代码

和业务无关的代码亦可放入图中作为节点托管（比如项目开发过程中的实验代码）。得益于 Cellink 对业务流的控制，这些非业务节点在正式的工作流程中永远不会执行。

当然如果你介意流程视图变得杂乱，可以选择定期清理一些非业务节点（注释掉它们的 @hook_parent 装饰器即可）。



### 实践三：重视中间结果的展示

直观的数据可视化对梳理业务逻辑很有帮助。可以为重要的节点实现 dump 或 show 方法，用于打印或可视化节点数据。甚至创建新的可视化节点来展示它们的内容。正如上面提到的那样，不要因此而担心影响运行速度（因为那不会发生）。



### 实践四：运用 Flag 节点

我们有时候会创建一些 Flag 节点来充当控制业务流的条件。比如某节点必须满足条件 A（比如说某个节点的变量大于 0 ）才能运行，那条件 A 就可以抽象成一个 Flag 节点：

``` python
@hook_parent(Number)
class FlagA(NodeSI): # 由条件 A 抽象出的节点
    def forward(self):
        return self.parent.val >= 0
    
@hook_parent(Number, FlagA)
class Sqrt(NodeMI):
	def forward(self):
        val = self.parent_list[0].val
        self.val = np.sqrt(val)
        return True
```

上面代码中，Sqrt 节点并没有访问 FlagA 的内容，而是利用 Cellink 的正向传播特性，把条件 A 变成自己运行的必要条件。

通常来说，条件 A 对业务很重要时我们才会把它抽象成 Flag 节点。这样做有利于业务逻辑的可视化（在流程视图上能直观反映）。

巧妙运用 NodeCI 节点还能实现其它基本逻辑（比如“异或”等）。



### 实践五：Worker 节点与 Neck 节点

worker 节点和 neck 节点来自项目实践，并非 Cellink 定义的特殊节点。本小节介绍如何借助这两种节点来实现检测任务。

- **worker 节点**：worker 节点都是叶子节点，名称以 'worker-' 开头。worker 节点通常是产生检测结果的节点，比如异常检测模块。worker 节点的检测结果通常在某 ROI 区域的局部坐标系。因此对外输出前，需要把局部坐标反向传播到根节点的全局坐标系上（见 backward 方法和 retr 方法）
- **neck 节点**：作为数据入口的根节点可以不直接面向各业务节点，而是通过一个 neck 节点代理数据分发。这样做的好处是方便 neck 节点在 backward 方法中收集反向传播回来的检测结果

下面代码展示了如何优雅地运行所有 worker 节点并收集它们的检测结果：

``` python
class InputNode(NodeSI):
    ...
    
@hook_parent(InputNode)
class Neck(NodeSI):
    ...
    def backward(self):
        if not hasattr(self.parent, 'results'):
            self.parent.results = self.results
        else:
            # 累积从不同 worker 节点反向传播回来的检测结果
            self.parent.results.extend(self.results)

# 运行所有 worker 节点，通过反向传播把检测结果累积到根节点
if __name__ == '__main__':
    root = InputNode.load_data(data)

    def _execute(node):
        if str(node).startswith('worker-') and node.seek(str(node)):
            node.retr()

    # 运行每一个 worker 节点并反向传播检测结果给根节点
    root.traverse(_execute)
    results = root.results
```



### 实践六：在节点中使用 Cellink

如果某个节点的业务很复杂，我们建议把它拆解成多个节点。但有时候这种拆解过于冗杂且与主业务无关（更不适合出现在流程视图上），我们就用子模块来封装该节点的业务。节点的子模块可以被另一个 Cellink 驱动，不同层级的 Cellink 不会相互干扰。




## Cellink 进阶

面向熟练使用者，Cellink 提供了一些高级特性。



### 量子节点

借用了量子力学的术语。Cellink 允许开发者构建所谓的“量子节点”。下图中的 Square 节点就是一个量子节点：

```python
class A(NodeSI):
    def forward(self):
        self.val = 12
        return True

class B(NodeSI):
    def forward(self):
        self.val = 2
        return True


@hook_parent([A, B])
class Square(NodeSI):
    def forward(self):
        val = self.parent.val
        self.val = val * val
        return True
```

表面上看，Square 节点与普通节点并无不同，但 Square 节点的“两个父节点”被放在方括号里。

这样的挂载方式在 Square 节点看来只挂载了一个父节点，但自己变成了两个分身。我们称 Square 节点处于**量子态**，它的量子态数量为 2 。

*量子节点本质上是共享一个节点名称和类定义的多个节点的集合。*

*某种意义上说，普通节点也是量子节点，它们的量子态数量为 1 。*



#### @hook_parent 的拓展

在更详细说明量子态之前，请允许我先介绍 @hook_parent 装饰器的拓展特性。

@hook_parent 装饰器完整的输入格式是：

```python
@hook_parent([(Node1, id1), (Node2, id2), ...], ...)
```

@hook_parent 装饰器的每个入参（Argument）代表一个父节点。它可以是一个节点类，或者 tuple 类型，或者节点类和 tuple 类型的混合列表（list）。这三种形式对挂载它的量子节点来说都是一个父节点。

其中 tuple 类型表示“坍缩”操作，用于析取量子节点的量子态。它的第一个元素为节点类，第二个元素为非负整数，表示所析取的第几个量子态：

```python
@hook_parent((Node, 0)) # 析取 Node 的第一个量子态作为父节点
@hook_parent((Node, 1)) # 析取 Node 的第二个量子态作为父节点
```

普通的挂载方式只是参数格式上的简化：

```python
# 假设 Node1 和 Node2 的量子态数量都为 1，即普通节点
# 以下两个表达式完全等价
@hook_parent(Node1, Node2, ...)
@hook_parent([(Node1, 0)], [(Node2, 0)])
```

@hook_parent 装饰器也支持混合格式：

```python
@hook_parent(Node1, (Node2, 1))
@hook_parent([Node1, (Node2, 2), Node3]， Node4)
```

@hook_parent 装饰器接收参数时的原则只有一个：所有父节点的量子态数量须保持一致。

这样做是为了保持父节点量子态之间的对应关系。因为子节点的量子态须和父节点的量子态一一对应。

假设一个多输入节点有两个父节点 Node1 和 Node2，那么一般来说 Node1 的量子态必须和 Node2 的相等。

然而也有例外。 @hook_parent 支持类似 numpy 里的 dimension broadcasting 。量子态为 1 的父节点会自动扩展自己的量子态，与其它父节点的量子态数量保持一致：

``` python
# 假设 Node1/2/3 都是量子态为 1 的普通节点
# 那以下输入格式也是合法的，因为 Node1 会自动扩展成 [Node1, Node1] 与 [Node2, Node3] 保持一致
@hook_parent(Node1, [Node2, Node3])

# 因为量子态的一一对应关系，上一条语句的效果类似于两个多输入类型的子节点挂载不同的父节点组合
@hook_parent(Node1, Node2) # 第一个量子态的等效
@hook_parent(Node1, Node3) # 第二个量子态的等效
```



#### 量子节点的特性

子节点的量子态数量和父节点的量子态数量相等。

在有量子节点的图中，traverse 方法只遍历所有节点的第一个量子态。

运行 seek 方法时，Cellink 会根据目标节点的量子态，选择其它节点相对应的量子态运行。

seek 量子节点的结果等效于 seek 该节点的第一个量子态。想要 seek 其它量子态，需要创建新节点并在 @hook_parent 装饰器里“坍缩”到想要的量子态：

```python
# 接之前的代码
@hook_parent((Square, 1))
class BSquare(NodeSI):
    def forward(self):
        self.val = self.parent.val
        return True

if __name__ == '__main__':
    node = A()
    node = node.seek('BSquare')
    print(node.val)
```

以上代码展示了如何从量子节点“坍缩”到普通节点。@hook_parent((Square, 1)) 表示挂载量子节点 Square 的第二个量子态，即和节点 B 对应的量子态。

输出结果是 4 。

下图是上面两段代码的流程视图：

![](assets/imgs/quantum-graph.png)