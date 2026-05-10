import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session, init_db
from app.services.auth_service import hash_password
from app.models.user import User
from app.models.product import Product
from app.models.order import Order
from app.models.document import Document
from app.ai.rag.chroma_store import index_documents, index_products


async def seed(db: AsyncSession):
    admin = User(
        name="管理员",
        phone="admin001",
        email="admin@omnisupport.ai",
        password_hash=hash_password("admin123"),
        role="admin",
        tags='["管理员"]',
    )
    user1 = User(
        name="张三",
        phone="13800138000",
        email="zhangsan@example.com",
        password_hash=hash_password("123456"),
        role="user",
        tags='["VIP", "高价值"]',
    )
    user2 = User(
        name="李四",
        phone="13900139000",
        email="lisi@example.com",
        password_hash=hash_password("123456"),
        role="user",
        tags='["新用户"]',
    )
    db.add_all([admin, user1, user2])
    await db.flush()

    products = [
        Product(name="iPhone 16 Pro Max 256GB", category="手机数码",
                price=9999.0, stock_quantity=128,
                description="Apple iPhone 16 Pro Max，6.9英寸 OLED 显示屏，A18 Pro 芯片，"
                            "256GB 存储，钛金属原色。支持 Apple Intelligence 功能。",
                specs='{"品牌":"Apple","屏幕":"6.9英寸 OLED","芯片":"A18 Pro","存储":"256GB","颜色":"钛金属原色"}'),
        Product(name="Samsung Galaxy S25 Ultra 256GB", category="手机数码",
                price=8999.0, stock_quantity=85,
                description="三星 Galaxy S25 Ultra，6.9英寸 Dynamic AMOLED 2X，骁龙 8 Gen 4 芯片，"
                            "2亿像素主摄，内置 S Pen，钛金属框架。Galaxy AI 全方位智能体验。",
                specs='{"品牌":"Samsung","屏幕":"6.9英寸 AMOLED","芯片":"骁龙8 Gen4","存储":"256GB","摄像头":"2亿像素"}'),
        Product(name="Xiaomi 15 Pro 512GB", category="手机数码",
                price=4999.0, stock_quantity=200,
                description="小米 15 Pro，6.73英寸 2K LTPO 屏幕，骁龙 8 Gen 4 芯片，"
                            "徕卡光学三摄，120W 有线快充+50W 无线快充，澎湃 OS 2.0。",
                specs='{"品牌":"Xiaomi","屏幕":"6.73英寸 2K","芯片":"骁龙8 Gen4","存储":"512GB","快充":"120W"}'),
        Product(name="OPPO Find X8 Pro 256GB", category="手机数码",
                price=4999.0, stock_quantity=150,
                description="OPPO Find X8 Pro，6.78英寸 AMOLED 曲面屏，天玑 9400 芯片，"
                            "哈苏四摄系统，100W 超级闪充，ColorOS 15，拍照旗舰标杆。",
                specs='{"品牌":"OPPO","屏幕":"6.78英寸 AMOLED","芯片":"天玑9400","存储":"256GB","快充":"100W"}'),
        Product(name="HUAWEI Pura 80 Pro 512GB", category="手机数码",
                price=5999.0, stock_quantity=110,
                description="华为 Pura 80 Pro，6.8英寸 OLED 昆仑玻璃屏，麒麟 9100 芯片，"
                            "XMAGE 影像系统，卫星通信，HarmonyOS NEXT 纯血鸿蒙。",
                specs='{"品牌":"HUAWEI","屏幕":"6.8英寸 OLED","芯片":"麒麟9100","存储":"512GB","特色":"卫星通信"}'),
        Product(name="MacBook Pro 14英寸 M4 Pro", category="电脑办公",
                price=16999.0, stock_quantity=56,
                description="Apple MacBook Pro 14英寸，M4 Pro 芯片 (12核CPU/16核GPU)，"
                            "18GB 统一内存，512GB SSD，Liquid Retina XDR 显示屏。适合专业开发与设计工作。",
                specs='{"品牌":"Apple","屏幕":"14英寸 Liquid Retina XDR","芯片":"M4 Pro","内存":"18GB","存储":"512GB SSD"}'),
        Product(name="ThinkPad X1 Carbon Gen 13", category="电脑办公",
                price=12999.0, stock_quantity=42,
                description="联想 ThinkPad X1 Carbon Gen 13，14英寸 2.8K OLED，Intel Core Ultra 9 285H，"
                            "32GB 内存，1TB SSD，碳纤维机身仅重 980g，通过 MIL-STD-810H 军规认证。",
                specs='{"品牌":"Lenovo","屏幕":"14英寸 2.8K OLED","芯片":"Core Ultra 9","内存":"32GB","存储":"1TB SSD"}'),
        Product(name="iPad Pro 13英寸 M4 2025", category="电脑办公",
                price=8999.0, stock_quantity=78,
                description="Apple iPad Pro 13英寸 M4，超 XDR 双层串联 OLED 屏，"
                            "Apple Pencil Pro 悬停功能，妙控键盘支持，轻薄便携创作神器。",
                specs='{"品牌":"Apple","屏幕":"13英寸 Ultra XDR OLED","芯片":"M4","存储":"256GB","配件":"Apple Pencil Pro"}'),
        Product(name="华为 MateBook X Pro 2025", category="电脑办公",
                price=10999.0, stock_quantity=35,
                description="华为 MateBook X Pro 2025，14.2英寸 3.1K OLED 原色屏，"
                            "Intel Core Ultra 9，32GB+1TB，Super Turbo 加速，超级终端多设备协同。",
                specs='{"品牌":"HUAWEI","屏幕":"14.2英寸 3.1K OLED","芯片":"Core Ultra 9","内存":"32GB","存储":"1TB SSD"}'),
        Product(name="ASUS ROG 幻16 Air RTX5070", category="电脑办公",
                price=13999.0, stock_quantity=28,
                description="华硕 ROG 幻16 Air，16英寸 2.5K 240Hz OLED，Core Ultra 9 + RTX 5070，"
                            "32GB+1TB，轻薄全能本，兼顾创作与电竞。",
                specs='{"品牌":"ASUS","屏幕":"16英寸 2.5K 240Hz OLED","芯片":"Core Ultra 9","GPU":"RTX 5070","存储":"1TB SSD"}'),
        Product(name="Sony WH-1000XM6 无线降噪耳机", category="影音娱乐",
                price=2499.0, stock_quantity=320,
                description="Sony 旗舰无线降噪耳机 WH-1000XM6，搭载 V2 集成降噪处理器，"
                            "支持 LDAC 高解析音频传输，续航 40 小时，支持快充。铂金银限定版。",
                specs='{"品牌":"Sony","类型":"头戴式无线","降噪":"主动降噪 V2","续航":"40小时","快充":"3分钟=3小时"}'),
        Product(name="AirPods Pro 第三代", category="影音娱乐",
                price=1799.0, stock_quantity=500,
                description="Apple AirPods Pro 3，H3 芯片，自适应主动降噪 2.0，"
                            "个性化空间音频，USB-C 充电盒带查找功能，IPX4 抗汗抗水。",
                specs='{"品牌":"Apple","类型":"入耳式真无线","降噪":"自适应降噪 2.0","芯片":"H3","续航":"6小时"}'),
        Product(name="Bose QuietComfort Ultra 耳机", category="影音娱乐",
                price=2699.0, stock_quantity=180,
                description="Bose QC Ultra 头戴式无线降噪耳机，Immersion 空间音频，"
                            "CustomTune 智能耳内调音，极致舒适佩戴，续航 30 小时。",
                specs='{"品牌":"Bose","类型":"头戴式无线","降噪":"CustomTune 自适应","续航":"30小时","特色":"空间音频"}'),
        Product(name="小米 Sound Pro 智能音箱", category="影音娱乐",
                price=899.0, stock_quantity=300,
                description="小米 Sound Pro，Harman 调音，40W 钕磁体扬声器，Hi-Res Audio 认证，"
                            "小爱同学 AI 大模型加持，全屋智能语音控制中枢。",
                specs='{"品牌":"Xiaomi","类型":"智能音箱","功率":"40W","认证":"Hi-Res Audio","特色":"小爱同学+AI大模型"}'),
        Product(name="JBL Flip 7 便携蓝牙音箱", category="影音娱乐",
                price=699.0, stock_quantity=400,
                description="JBL Flip 7 便携蓝牙音箱，IP67 防水防尘，20 小时续航，"
                            "PartyBoost 串联多台，JBL 标志性低音。户外露营必备。",
                specs='{"品牌":"JBL","类型":"便携蓝牙音箱","防水":"IP67","续航":"20小时","特色":"PartyBoost串联"}'),
        Product(name="DJI Mini 4 Pro 无人机畅飞套装", category="智能设备",
                price=5988.0, stock_quantity=73,
                description="DJI Mini 4 Pro 超轻无人机，249g 无需登记，4K/100fps 视频，"
                            "全向避障，34 分钟续航。畅飞套装含 3 块电池和充电管家。",
                specs='{"品牌":"DJI","重量":"249g","视频":"4K/100fps","续航":"34分钟","避障":"全向避障"}'),
        Product(name="Apple Watch Ultra 3", category="智能设备",
                price=5999.0, stock_quantity=60,
                description="Apple Watch Ultra 3，49mm 钛金属表壳，S5 SiP 芯片，"
                            "双频 GPS，2000 尼特亮度，100m 防水，潜水电脑+登山向导。",
                specs='{"品牌":"Apple","尺寸":"49mm","芯片":"S5 SiP","续航":"72小时","防水":"100m WR100"}'),
        Product(name="DJI Osmo Pocket 4", category="智能设备",
                price=3499.0, stock_quantity=95,
                description="DJI Osmo Pocket 4 口袋云台相机，1英寸 CMOS，4K/120fps，"
                            "3 轴机械云台，ActiveTrack 6.0 智能跟随，Vlog 创作者利器。",
                specs='{"品牌":"DJI","传感器":"1英寸 CMOS","视频":"4K/120fps","稳定":"3轴机械云台","特色":"智能跟随6.0"}'),
        Product(name="小米智能手环 9 Pro", category="智能设备",
                price=399.0, stock_quantity=600,
                description="小米智能手环 9 Pro，1.74英寸 AMOLED 屏，100+ 运动模式，"
                            "血氧/心率/睡眠监测，14 天超长续航，NFC 公交门禁。",
                specs='{"品牌":"Xiaomi","屏幕":"1.74英寸 AMOLED","模式":"100+运动","续航":"14天","特色":"NFC+血氧监测"}'),
        Product(name="Insta360 X5 全景相机", category="智能设备",
                price=2999.0, stock_quantity=120,
                description="Insta360 X5 全景运动相机，8K全景视频，FlowState 防抖，"
                            "AI 自动取景剪辑，子弹时间，10m 裸机防水。创意无限的随身相机。",
                specs='{"品牌":"Insta360","视频":"8K全景","防水":"10m","防抖":"FlowState 3.0","特色":"AI自动取景"}'),
        Product(name="戴森 V15 Detect 无绳吸尘器", category="生活家电",
                price=4990.0, stock_quantity=91,
                description="Dyson V15 Detect 无绳手持吸尘器，激光探测微尘技术，"
                            "压电式传感器实时显示吸入颗粒，240AW 强劲吸力，60 分钟续航。",
                specs='{"品牌":"Dyson","型号":"V15 Detect","吸力":"240AW","续航":"60分钟","特色":"激光探测+传感器"}'),
        Product(name="石头 G30 自清洁扫拖机器人", category="生活家电",
                price=3999.0, stock_quantity=130,
                description="石头 G30 扫拖机器人，双旋转拖布+自动抬升，11000Pa 吸力，"
                            "LDS 激光导航+3D 结构光避障，自动洗拖布/烘干/加水/排污水全能基站。",
                specs='{"品牌":"Roborock","吸力":"11000Pa","导航":"LDS+3D结构光","基站":"自动洗烘/加水/排污","特色":"双旋转拖布"}'),
        Product(name="戴森 Purifier Hot+Cool HP10", category="生活家电",
                price=4690.0, stock_quantity=55,
                description="戴森 HP10 空气净化器+暖风扇+冷风扇三合一，HEPA H13+活性炭过滤，"
                            "整屋净化+精准控温，Air Multiplier 气流倍增技术。一年四季皆可用。",
                specs='{"品牌":"Dyson","过滤":"HEPA H13+活性炭","功能":"净化+暖风+冷风","特色":"Air Multiplier气流倍增"}'),
        Product(name="追觅 H40 无线洗地机", category="生活家电",
                price=3299.0, stock_quantity=100,
                description="追觅 H40 无线洗地机，18000Pa 吸力，滚刷自清洁+热风烘干，"
                            "污水箱固液分离，贴边清洁设计，一推即净不留水渍。",
                specs='{"品牌":"Dreame","吸力":"18000Pa","特色":"自清洁+热风烘干","续航":"40分钟","设计":"贴边清洁"}'),
        Product(name="飞利浦 Sonicare 9900 电动牙刷", category="生活家电",
                price=1499.0, stock_quantity=250,
                description="飞利浦旗舰级 Sonicare 9900 声波电动牙刷，31000 次/分钟震频，"
                            "SenseIQ 智能感应+压力保护，4 种模式+3 档强度，充电一次用 3 周。",
                specs='{"品牌":"Philips","震频":"31000次/分钟","模式":"4种+3档强度","续航":"3周","特色":"SenseIQ智能感应"}'),
    ]
    db.add_all(products)
    await db.flush()

    orders = [
        Order(
            user_id=user1.id,
            status="delivered",
            total_amount=9999.0,
            payment_method="银行转账",
            logistics_status='{"status": "已签收", "delivered_at": "2025-03-20"}',
            items='[{"product_id": 1, "name": "iPhone 16 Pro Max 256GB", "quantity": 1, "price": 9999.0}]',
        ),
        Order(
            user_id=user1.id,
            status="shipped",
            total_amount=2499.0,
            payment_method="微信支付",
            logistics_no="SF1234567890",
            logistics_status='{"status": "运输中", "estimated_delivery": "2025-05-10"}',
            items='[{"product_id": 11, "name": "Sony WH-1000XM6 无线降噪耳机", "quantity": 1, "price": 2499.0}]',
        ),
        Order(
            user_id=user1.id,
            status="paid",
            total_amount=13999.0,
            payment_method="信用卡分期",
            items='[{"product_id": 10, "name": "ASUS ROG 幻16 Air RTX5070", "quantity": 1, "price": 13999.0}]',
        ),
        Order(
            user_id=user2.id,
            status="pending",
            total_amount=5988.0,
            payment_method="支付宝",
            items='[{"product_id": 16, "name": "DJI Mini 4 Pro 无人机畅飞套装", "quantity": 1, "price": 5988.0}]',
        ),
        Order(
            user_id=user2.id,
            status="shipped",
            total_amount=4999.0,
            payment_method="微信支付",
            logistics_no="YTO9876543210",
            logistics_status='{"status": "已揽件", "estimated_delivery": "2025-05-12"}',
            items='[{"product_id": 3, "name": "Xiaomi 15 Pro 512GB", "quantity": 1, "price": 4999.0}]',
        ),
        Order(
            user_id=user2.id,
            status="delivered",
            total_amount=5798.0,
            payment_method="花呗",
            logistics_status='{"status": "已签收", "delivered_at": "2025-02-15"}',
            items='[{"product_id": 21, "name": "戴森 V15 Detect 无绳吸尘器", "quantity": 1, "price": 4990.0},'
                  '{"product_id": 25, "name": "飞利浦 Sonicare 9900 电动牙刷", "quantity": 1, "price": 1499.0}]',
        ),
    ]
    db.add_all(orders)
    await db.flush()

    docs = [
        Document(
            title="iPhone 16 Pro Max 产品介绍与常见问题",
            content="iPhone 16 Pro Max 是 Apple 2024 年发布的旗舰手机。配备 6.9 英寸 Super Retina XDR OLED 显示屏，"
                    "支持 120Hz ProMotion 自适应刷新率。搭载 A18 Pro 芯片，采用第二代 3nm 制程，CPU 性能提升 15%，"
                    "GPU 支持硬件级光线追踪。256GB 存储起步，最高可选 1TB。支持 Apple Intelligence 个人智能系统，"
                    "可进行实时语音转录、图片生成和智能通知管理。常见问题：支持 5G 网络吗？所有 iPhone 16 系列均支持 5G 全网通。"
                    "支持无线充电吗？支持 MagSafe 25W 磁吸无线快充和 Qi2 标准无线充电。"
                    "防水吗？具备 IP68 级防水防尘，可在 6 米水深停留 30 分钟。"
                    "颜色选择有哪些？钛金属原色、钛金属蓝色、钛金属白色和钛金属黑色四种。",
            chunk_index=0,
            source_url="https://www.apple.com/cn/iphone-16-pro/",
        ),
        Document(
            title="MacBook Pro 14英寸 M4 Pro 产品介绍",
            content="MacBook Pro 14英寸（M4 Pro 芯片）定位专业级移动工作站。M4 Pro 芯片拥有 12 核 CPU + 16 核 GPU，"
                    "统一内存带宽高达 273GB/s。18GB 内存起步，可选配至 36GB。14.2 英寸 Liquid Retina XDR 显示屏，"
                    "峰值亮度达 1600 尼特（HDR），支持 10 亿色彩和 P3 广色域，极为适合摄影、设计、视频剪辑等专业工作。"
                    "续航达 17 小时视频播放，配备三个雷雳 5 接口和一个 HDMI 接口。常见问题：适合程序员吗？非常适合，"
                    "编译速度快，Xcode 和 VS Code 运行流畅，Docker 和虚拟机性能强劲。"
                    "能外接几个显示器？最多支持两台 6K 外接显示器（60Hz）。"
                    "和 M3 Pro 款有什么差别？M4 Pro CPU 多 2 个核心，雷雳接口从 4 升级到 5，SSD 读取速度更快。",
            chunk_index=0,
            source_url="https://www.apple.com/cn/macbook-pro/",
        ),
        Document(
            title="Sony WH-1000XM6 无线降噪耳机",
            content="Sony WH-1000XM6 是索尼 2025 年旗舰头戴式无线降噪耳机。搭载集成处理器 V2 + HD 降噪处理器 QN2e 双芯片，"
                    "主动降噪能力相比 XM5 提升 20%。支持 LDAC 高解析音频传输（990kbps）和 DSEE Extreme 数字声音增强引擎，"
                    "可实时提升压缩音频的音质至接近高解析度水平。续航时间 40 小时（开降噪），支持快充：充电 3 分钟播放 3 小时。"
                    "佩戴检测功能可在取下耳机时自动暂停音乐。多点连接支持同时连接两台设备。"
                    "常见问题：适合运动佩戴吗？XM6 为头戴式设计，日常通勤和办公很棒，但剧烈运动建议用入耳式。"
                    "连接稳定性如何？蓝牙 5.4，支持 LE Audio 和 LC3 编解码，连接稳定无延迟。"
                    "铂金银和黑色怎么选？铂金银质感更高级不易沾指纹，黑色经典耐脏。",
            chunk_index=0,
            source_url="https://www.sony.com/electronics/headband-headphones/wh-1000xm6",
        ),
        Document(
            title="DJI Mini 4 Pro 无人机",
            content="DJI Mini 4 Pro 是 DJI 2024 年推出的超轻型航拍无人机，起飞重量仅 249g，根据民航法规无需实名登记即可飞行。"
                    "配备 1/1.3 英寸 CMOS 传感器，支持 4K/100fps 超高清视频录制和 HDR 视频，"
                    "可实现 D-Log M 专业色彩模式和 10-bit 色深。全向避障系统：前、后、左、右、上五向双目视觉 + 下视 ToF 传感器。"
                    "续航 34 分钟（标准电池），畅飞套装含 3 块电池和双向充电管家，总飞行时间可达 102 分钟。"
                    "O4 图传系统最远传输距离 20 公里。常见问题：需要考无人机驾照吗？249g 以下的 Mini 4 Pro 无需驾照和登记。"
                    "适合新手吗？支持一键起降、自动返航、智能跟随，操作零门槛。"
                    "抗风能力如何？5 级抗风（最高 10.7m/s），风力较大时建议谨慎飞行。"
                    "充电管家有什么用？可同时为三块电池充电，支持 PD 快充，还能当移动电源为遥控器充电。",
            chunk_index=0,
            source_url="https://www.dji.com/cn/mini-4-pro",
        ),
        Document(
            title="戴森 Dyson V15 Detect 无绳吸尘器",
            content="Dyson V15 Detect 是戴森 2024 年旗舰无绳手持吸尘器。搭载 Dyson Hyperdymium 数码马达，转速达 125,000rpm，"
                    "最大吸力 240AW（空气瓦特），比上一代 V12 提升 60%。激光探测微尘技术：主吸头内置绿色激光二极管，"
                    "将地面上肉眼不可见的微尘颗粒可视化呈现，确保彻底清洁。压电式声学传感器实时检测吸入的颗粒大小和数量，"
                    "数据通过 LCD 屏幕实时显示，让清洁效果一目了然。续航 60 分钟（节能模式），可更换电池设计延长清洁时间。"
                    "配备 6 款吸头：激光软绒吸头（硬地板）、防缠绕螺旋吸头（床褥除螨）、窄缝吸头（角落）等。"
                    "常见问题：宠物家庭适合吗？防缠绕螺旋吸头专为宠物毛发设计，不会缠绕刷头。"
                    "电池能换吗？电池可拆卸，长按电池释放按钮即可更换，建议额外配备一块电池用于大户型。"
                    "滤网多久清洗？建议每月清洗一次，清水冲洗后自然晾干 24 小时即可。",
            chunk_index=0,
            source_url="https://www.dyson.cn/vacuum-cleaners/cordless/v15/detect",
        ),
        Document(
            title="退换货政策",
            content="本商城退换货政策如下：一、7 天无理由退货：自签收之日起 7 天内，商品完好（未激活、无人为损坏、配件齐全），"
                    "可申请无理由退货。运费由买家承担（质量问题除外）。二、15 天内质量问题换货：签收后 15 天内，如商品出现"
                    "非人为因素造成的功能性故障，经售后检测确认后可更换同型号新品。三、一年保修：手机、电脑等数码产品享一年"
                    "官方质保；耳机、无人机、吸尘器等享一年全国联保。四、不支持退货的情形：已激活的手机/电脑（激活后会影响"
                    "二次销售）、已拆封的耳机（卫生原因）、已使用的耗材配件。五、退款时效：退回商品验收合格后，退款将在 3-5 个"
                    "工作日内原路返回。退款金额超过 500 元需人工审批。六、退换货流程：1) 联系客服提交申请 → 2) 获取退换货"
                    "地址和运单号 → 3) 寄回商品 → 4) 仓库验收 → 5) 退款/换货。",
            chunk_index=0,
            source_url="https://shop.example.com/return-policy",
        ),
        Document(
            title="物流配送说明",
            content="本商城物流配送说明：一、配送方式：全国顺丰包邮（部分偏远地区可能产生额外运费）。默认使用顺丰速运，"
                    "支持陆运和空运。二、发货时效：工作日 16:00 前下单当天发货，16:00 后次日发货；周末及节假日顺延至"
                    "下一个工作日。预售商品按页面标注的发货日期发货。三、配送时效：一线城市 1-2 天送达，省会城市 2-3 天，"
                    "其他地区 3-5 天。偏远地区（新疆、西藏、青海等）5-7 天。四、物流追踪：发货后系统自动推送物流单号，"
                    "您可登录账号在订单详情中查看实时物流状态，也可通过顺丰官网或 APP 使用运单号查询。"
                    "五、签收须知：签收前请确认包裹外包装完好，如发现破损、变形请拒收并联系客服。"
                    "贵重商品（单价超 5000 元）建议开箱验货后签收。六、物流异常处理：如遇丢件、破损等异常情况，"
                    "请联系客服，我们将在 24 小时内与物流公司核实并优先为您补发。",
            chunk_index=0,
            source_url="https://shop.example.com/shipping",
        ),
        Document(
            title="售后服务与保修政策",
            content="本商城售后服务与保修政策：一、全品类一年保修：所有商品自购买之日起享一年全国联保。"
                    "保修期内出现非人为质量问题，免费维修或更换。二、延保服务：手机和电脑可额外购买延保（+299元/年，"
                    "最长延保 2 年），延保期内意外损坏（碎屏、进水等）享 5 折维修优惠。三、售后流程："
                    "1) 联系在线客服描述问题 → 2) 客服判断故障类型并给出处理方案 → 3) 需返修的，客服安排顺丰上门取件 → "
                    "4) 维修中心检测维修（通常 3-5 个工作日）→ 5) 修好后顺丰寄回。四、常见售后场景："
                    "手机屏幕碎了怎么办？人为损坏不在保修范围内，可付费维修，iPhone 16 Pro Max 屏幕维修参考价 3199 元。"
                    "耳机一只不响了？在保修期内可免费换新。无人机飞丢了怎么办？DJI Care Refresh 可享低价置换服务。"
                    "吸尘器吸力变弱了？先清洗滤网和刷头，若仍无效可寄回检测，保修期内免费处理。"
                    "五、客服联系方式：在线客服 7x24 小时服务，人工坐席工作时间 9:00-21:00。",
            chunk_index=0,
            source_url="https://shop.example.com/warranty",
        ),
    ]
    db.add_all(docs)
    await db.commit()

    doc_tuples = [(d.id, d.title, d.content) for d in docs]
    await index_documents(doc_tuples)

    prod_tuples = [(p.id, p.name, p.category, p.description) for p in products]
    await index_products(prod_tuples)

    print("Seed data created successfully!")
    print("  Admin: admin001 / admin123")
    print("  User 1: 13800138000 / 123456")
    print("  User 2: 13900139000 / 123456")


async def main():
    await init_db()
    async with async_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(User))
        if result.first():
            print("Database already contains data. Skipping seed.")
            return
        await seed(session)


if __name__ == "__main__":
    asyncio.run(main())
