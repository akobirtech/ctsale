"""Katalogning boshlang'ich ma'lumotlari.

Seed komandasi shu yerdan o'qiydi. Admin panelda keyinchalik
o'zgartirish mumkin — bu faqat boshlang'ich holat.
"""

# --------------------------------------------------------------------------
# Hududlar: (uz, ru, en, [tumanlar])
# --------------------------------------------------------------------------
REGIONS = [
    ("Toshkent shahri", "город Ташкент", "Tashkent City", [
        "Bektemir", "Chilonzor", "Mirobod", "Mirzo Ulug'bek", "Olmazor",
        "Sergeli", "Shayxontohur", "Uchtepa", "Yakkasaroy", "Yashnobod",
        "Yunusobod", "Yangihayot",
    ]),
    ("Toshkent viloyati", "Ташкентская область", "Tashkent Region", [
        "Angren", "Bekobod", "Chirchiq", "Nurafshon", "Olmaliq",
        "Ohangaron", "Parkent", "Piskent", "Yangiyo'l", "Zangiota",
    ]),
    ("Andijon", "Андижан", "Andijan", [
        "Andijon shahri", "Asaka", "Xonabod", "Shahrixon", "Marhamat",
    ]),
    ("Buxoro", "Бухара", "Bukhara", [
        "Buxoro shahri", "G'ijduvon", "Kogon", "Romitan", "Vobkent",
    ]),
    ("Farg'ona", "Фергана", "Fergana", [
        "Farg'ona shahri", "Marg'ilon", "Qo'qon", "Quva", "Rishton",
    ]),
    ("Jizzax", "Джизак", "Jizzakh", ["Jizzax shahri", "G'allaorol", "Zomin", "Sharof Rashidov"]),
    ("Namangan", "Наманган", "Namangan", [
        "Namangan shahri", "Chust", "Kosonsoy", "Pop", "To'raqo'rg'on",
    ]),
    ("Navoiy", "Навои", "Navoi", ["Navoiy shahri", "Zarafshon", "Karmana", "Qiziltepa"]),
    ("Qashqadaryo", "Кашкадарья", "Kashkadarya", [
        "Qarshi", "Shahrisabz", "Kitob", "G'uzor", "Koson",
    ]),
    ("Qoraqalpog'iston", "Каракалпакстан", "Karakalpakstan", [
        "Nukus", "Xo'jayli", "Beruniy", "Chimboy", "To'rtko'l",
    ]),
    ("Samarqand", "Самарканд", "Samarkand", [
        "Samarqand shahri", "Kattaqo'rg'on", "Urgut", "Bulung'ur", "Jomboy",
    ]),
    ("Sirdaryo", "Сырдарья", "Syrdarya", ["Guliston", "Yangiyer", "Shirin", "Boyovut"]),
    ("Surxondaryo", "Сурхандарья", "Surkhandarya", [
        "Termiz", "Denov", "Sherobod", "Boysun", "Sho'rchi",
    ]),
    ("Xorazm", "Хорезм", "Khorezm", ["Urganch", "Xiva", "Shovot", "Gurlan", "Xonqa"]),
]

# --------------------------------------------------------------------------
# Kategoriyalar: (slug, uz, ru, en, ikonka, bosh sahifada?, [ichki])
# --------------------------------------------------------------------------
CATEGORIES = [
    ("noutbuklar", "Noutbuklar", "Ноутбуки", "Laptops", "laptop", True, [
        ("gaming-noutbuklar", "Gaming noutbuklar", "Игровые ноутбуки", "Gaming Laptops"),
        ("ultrabuklar", "Ultrabuklar", "Ультрабуки", "Ultrabooks"),
        ("ishchi-stansiyalar", "Ishchi stansiyalar", "Рабочие станции", "Workstations"),
        ("byudjet-noutbuklar", "Byudjet noutbuklar", "Бюджетные ноутбуки", "Budget Laptops"),
        ("macbook", "MacBook", "MacBook", "MacBook"),
    ]),
    ("kompyuterlar", "Kompyuterlar", "Компьютеры", "Desktop PCs", "monitor", True, [
        ("gaming-pk", "Gaming PK", "Игровые ПК", "Gaming PCs"),
        ("ofis-kompyuterlar", "Ofis kompyuterlari", "Офисные ПК", "Office PCs"),
        ("mini-pk", "Mini PK", "Мини ПК", "Mini PCs"),
        ("all-in-one", "All-in-One", "Моноблоки", "All-in-One"),
        ("imac-mac", "iMac / Mac", "iMac / Mac", "iMac / Mac"),
    ]),
    ("videokartalar", "Videokartalar", "Видеокарты", "Graphics Cards", "cpu", True, [
        ("nvidia-geforce", "NVIDIA GeForce", "NVIDIA GeForce", "NVIDIA GeForce"),
        ("amd-radeon", "AMD Radeon", "AMD Radeon", "AMD Radeon"),
        ("intel-arc", "Intel Arc", "Intel Arc", "Intel Arc"),
        ("professional-gpu", "Professional GPU", "Профессиональные GPU", "Professional GPU"),
    ]),
    ("protsessorlar", "Protsessorlar", "Процессоры", "Processors", "cpu", True, [
        ("intel-cpu", "Intel", "Intel", "Intel"),
        ("amd-cpu", "AMD", "AMD", "AMD"),
    ]),
    ("monitorlar", "Monitorlar", "Мониторы", "Monitors", "monitor", True, [
        ("gaming-monitorlar", "Gaming monitorlar", "Игровые мониторы", "Gaming Monitors"),
        ("professional-monitorlar", "Professional monitorlar", "Профессиональные", "Professional"),
        ("ofis-monitorlar", "Ofis monitorlari", "Офисные мониторы", "Office Monitors"),
    ]),
    ("operativ-xotira", "Operativ xotira (RAM)", "Оперативная память", "Memory (RAM)", "memory-stick", True, [
        ("ddr4", "DDR4", "DDR4", "DDR4"),
        ("ddr5", "DDR5", "DDR5", "DDR5"),
        ("noutbuk-ram", "Noutbuk uchun (SODIMM)", "Для ноутбуков", "Laptop (SODIMM)"),
    ]),
    ("saqlash-qurilmalari", "Saqlash qurilmalari", "Накопители", "Storage", "hard-drive", True, [
        ("ssd-nvme", "SSD NVMe", "SSD NVMe", "SSD NVMe"),
        ("ssd-sata", "SSD SATA", "SSD SATA", "SSD SATA"),
        ("hdd", "Qattiq disk (HDD)", "Жёсткие диски", "Hard Drives"),
        ("tashqi-disklar", "Tashqi disklar", "Внешние диски", "External Drives"),
    ]),
    ("ona-platalar", "Ona platalar", "Материнские платы", "Motherboards", "circuit-board", True, [
        ("intel-platform", "Intel platformasi", "Платформа Intel", "Intel Platform"),
        ("amd-platform", "AMD platformasi", "Платформа AMD", "AMD Platform"),
    ]),
    ("quvvat-bloklari", "Quvvat bloklari (PSU)", "Блоки питания", "Power Supplies", "plug-zap", False, []),
    ("korpuslar", "Korpuslar", "Корпуса", "Cases", "box", False, []),
    ("sovutish", "Sovutish tizimlari", "Охлаждение", "Cooling", "fan", False, [
        ("havo-sovutish", "Havo sovutish", "Воздушное охлаждение", "Air Cooling"),
        ("suyuqlik-sovutish", "Suyuqlik sovutish", "Жидкостное охлаждение", "Liquid Cooling"),
        ("korpus-ventilyatorlari", "Korpus ventilyatorlari", "Корпусные вентиляторы", "Case Fans"),
    ]),
    ("klaviaturalar", "Klaviaturalar", "Клавиатуры", "Keyboards", "keyboard", True, [
        ("mexanik-klaviatura", "Mexanik", "Механические", "Mechanical"),
        ("membrana-klaviatura", "Membranali", "Мембранные", "Membrane"),
        ("simsiz-klaviatura", "Simsiz", "Беспроводные", "Wireless"),
    ]),
    ("sichqonchalar", "Sichqonchalar", "Мыши", "Mice", "mouse-pointer", True, [
        ("gaming-sichqoncha", "Gaming", "Игровые", "Gaming"),
        ("ofis-sichqoncha", "Ofis", "Офисные", "Office"),
    ]),
    ("quloqchinlar", "Quloqchinlar", "Наушники", "Headsets", "headphones", True, [
        ("gaming-quloqchin", "Gaming quloqchinlar", "Игровые наушники", "Gaming Headsets"),
        ("simsiz-quloqchin", "Simsiz quloqchinlar", "Беспроводные", "Wireless"),
    ]),
    ("veb-kameralar", "Veb-kameralar", "Веб-камеры", "Webcams", "video", False, []),
    ("printerlar", "Printerlar va MFU", "Принтеры и МФУ", "Printers", "printer", False, [
        ("lazerli-printer", "Lazerli", "Лазерные", "Laser"),
        ("siyohli-printer", "Siyohli", "Струйные", "Inkjet"),
        ("mfu", "MFU", "МФУ", "All-in-One"),
    ]),
    ("tarmoq", "Tarmoq uskunalari", "Сетевое оборудование", "Networking", "network", False, [
        ("routerlar", "Routerlar", "Роутеры", "Routers"),
        ("switchlar", "Switchlar", "Коммутаторы", "Switches"),
        ("tarmoq-kartalari", "Tarmoq kartalari", "Сетевые карты", "Network Cards"),
    ]),
    ("planshetlar", "Planshetlar", "Планшеты", "Tablets", "tablet", False, []),
    ("aksessuarlar", "Aksessuarlar", "Аксессуары", "Accessories", "cable", False, [
        ("kabellar", "Kabellar va adapterlar", "Кабели и адаптеры", "Cables & Adapters"),
        ("sumkalar", "Sumkalar va g'iloflar", "Сумки и чехлы", "Bags & Cases"),
        ("sichqoncha-kilimchalari", "Sichqoncha kilimchalari", "Коврики", "Mousepads"),
        ("ups", "UPS", "ИБП", "UPS"),
    ]),
    ("boshqa", "Boshqa", "Прочее", "Other", "package", False, []),
]

# --------------------------------------------------------------------------
# Brendlar: (nom, ommabopmi)
# --------------------------------------------------------------------------
BRANDS = [
    ("ASUS", True), ("Lenovo", True), ("HP", True), ("Dell", True), ("Acer", True),
    ("Apple", True), ("MSI", True), ("Gigabyte", True), ("NVIDIA", True), ("AMD", True),
    ("Intel", True), ("Samsung", True), ("Kingston", True), ("Corsair", True),
    ("Logitech", True), ("Razer", True), ("Western Digital", False), ("Seagate", False),
    ("Crucial", False), ("ADATA", False), ("Cooler Master", False), ("NZXT", False),
    ("be quiet!", False), ("Thermaltake", False), ("Zotac", False), ("Palit", False),
    ("Sapphire", False), ("ASRock", False), ("Huawei", False), ("Xiaomi", False),
    ("HyperX", False), ("SteelSeries", False), ("A4Tech", False), ("Canon", False),
    ("Epson", False), ("Brother", False), ("TP-Link", False), ("Mikrotik", False),
    ("Transcend", False), ("Patriot", False),
]

# --------------------------------------------------------------------------
# Xususiyatlar: kategoriya slug -> ro'yxat
# (code, uz, ru, en, tur, birlik, majburiy, filtrda, kartada, [variantlar])
# --------------------------------------------------------------------------
T_TEXT, T_INT, T_DEC, T_BOOL, T_SEL = "text", "integer", "decimal", "boolean", "select"

ATTRIBUTES = {
    "noutbuklar": [
        ("cpu", "Protsessor", "Процессор", "CPU", T_TEXT, "", True, True, True, []),
        ("ram_gb", "Operativ xotira", "Оперативная память", "RAM", T_INT, "GB", True, True, True, []),
        ("storage_gb", "Xotira hajmi", "Объём накопителя", "Storage", T_INT, "GB", True, True, True, []),
        ("storage_type", "Xotira turi", "Тип накопителя", "Storage Type", T_SEL, "", False, True, False,
         [("ssd_nvme", "SSD NVMe"), ("ssd_sata", "SSD SATA"), ("hdd", "HDD"), ("ssd_hdd", "SSD + HDD")]),
        ("gpu", "Videokarta", "Видеокарта", "GPU", T_TEXT, "", False, True, True, []),
        ("screen_inch", "Ekran o'lchami", "Размер экрана", "Screen Size", T_DEC, '"', True, True, True, []),
        ("resolution", "Ekran aniqligi", "Разрешение", "Resolution", T_SEL, "", False, True, False,
         [("1366x768", "1366x768 (HD)"), ("1920x1080", "1920x1080 (FHD)"),
          ("2560x1440", "2560x1440 (QHD)"), ("2560x1600", "2560x1600 (WQXGA)"),
          ("3840x2160", "3840x2160 (4K)")]),
        ("refresh_hz", "Yangilanish chastotasi", "Частота обновления", "Refresh Rate", T_INT, "Hz", False, True, False, []),
        ("os", "Operatsion tizim", "Операционная система", "OS", T_SEL, "", False, True, False,
         [("win11", "Windows 11"), ("win10", "Windows 10"), ("macos", "macOS"),
          ("linux", "Linux"), ("dos", "DOS / OS yo'q")]),
        ("battery_wh", "Batareya sig'imi", "Ёмкость батареи", "Battery", T_INT, "Wh", False, False, False, []),
        ("weight_kg", "Og'irligi", "Вес", "Weight", T_DEC, "kg", False, False, False, []),
    ],
    "kompyuterlar": [
        ("cpu", "Protsessor", "Процессор", "CPU", T_TEXT, "", True, True, True, []),
        ("ram_gb", "Operativ xotira", "Оперативная память", "RAM", T_INT, "GB", True, True, True, []),
        ("gpu", "Videokarta", "Видеокарта", "GPU", T_TEXT, "", False, True, True, []),
        ("storage_gb", "Xotira hajmi", "Объём накопителя", "Storage", T_INT, "GB", True, True, True, []),
        ("psu_watt", "Quvvat bloki", "Блок питания", "PSU", T_INT, "W", False, False, False, []),
        ("form_factor", "Korpus turi", "Форм-фактор", "Form Factor", T_SEL, "", False, True, False,
         [("full_tower", "Full Tower"), ("mid_tower", "Mid Tower"),
          ("mini_itx", "Mini-ITX"), ("sff", "Small Form Factor")]),
    ],
    "videokartalar": [
        ("vram_gb", "Video xotira", "Видеопамять", "VRAM", T_INT, "GB", True, True, True, []),
        ("memory_type", "Xotira turi", "Тип памяти", "Memory Type", T_SEL, "", False, True, False,
         [("gddr6", "GDDR6"), ("gddr6x", "GDDR6X"), ("gddr7", "GDDR7"),
          ("gddr5", "GDDR5"), ("hbm2", "HBM2")]),
        ("memory_bus", "Xotira shinasi", "Шина памяти", "Memory Bus", T_INT, "bit", False, True, False, []),
        ("tdp_watt", "Energiya iste'moli", "Энергопотребление", "TDP", T_INT, "W", False, False, False, []),
        ("interface", "Interfeys", "Интерфейс", "Interface", T_SEL, "", False, True, False,
         [("pcie4", "PCIe 4.0 x16"), ("pcie5", "PCIe 5.0 x16"), ("pcie3", "PCIe 3.0 x16")]),
        ("outputs", "Chiqish portlari", "Выходы", "Outputs", T_TEXT, "", False, False, False, []),
        ("length_mm", "Uzunligi", "Длина", "Length", T_INT, "mm", False, False, False, []),
    ],
    "protsessorlar": [
        ("socket", "Soket", "Сокет", "Socket", T_TEXT, "", True, True, True, []),
        ("cores", "Yadrolar soni", "Количество ядер", "Cores", T_INT, "", True, True, True, []),
        ("threads", "Oqimlar soni", "Потоки", "Threads", T_INT, "", False, True, False, []),
        ("base_ghz", "Bazaviy chastota", "Базовая частота", "Base Clock", T_DEC, "GHz", False, True, False, []),
        ("boost_ghz", "Turbo chastota", "Турбо частота", "Boost Clock", T_DEC, "GHz", False, True, True, []),
        ("tdp_watt", "TDP", "TDP", "TDP", T_INT, "W", False, False, False, []),
        ("integrated_gpu", "Integratsiyalangan grafika", "Встроенная графика", "iGPU", T_BOOL, "", False, True, False, []),
    ],
    "monitorlar": [
        ("screen_inch", "Diagonal", "Диагональ", "Size", T_DEC, '"', True, True, True, []),
        ("resolution", "Aniqlik", "Разрешение", "Resolution", T_SEL, "", True, True, True,
         [("1920x1080", "1920x1080 (FHD)"), ("2560x1440", "2560x1440 (QHD)"),
          ("3440x1440", "3440x1440 (UWQHD)"), ("3840x2160", "3840x2160 (4K)")]),
        ("refresh_hz", "Yangilanish chastotasi", "Частота обновления", "Refresh Rate", T_INT, "Hz", True, True, True, []),
        ("panel_type", "Matritsa turi", "Тип матрицы", "Panel Type", T_SEL, "", False, True, False,
         [("ips", "IPS"), ("va", "VA"), ("tn", "TN"), ("oled", "OLED"), ("qd_oled", "QD-OLED")]),
        ("response_ms", "Javob vaqti", "Время отклика", "Response Time", T_DEC, "ms", False, True, False, []),
        ("ports", "Portlar", "Порты", "Ports", T_TEXT, "", False, False, False, []),
        ("curved", "Egri ekran", "Изогнутый", "Curved", T_BOOL, "", False, True, False, []),
    ],
    "operativ-xotira": [
        ("capacity_gb", "Hajmi", "Объём", "Capacity", T_INT, "GB", True, True, True, []),
        ("memory_type", "Turi", "Тип", "Type", T_SEL, "", True, True, True,
         [("ddr3", "DDR3"), ("ddr4", "DDR4"), ("ddr5", "DDR5")]),
        ("speed_mhz", "Chastota", "Частота", "Speed", T_INT, "MHz", False, True, True, []),
        ("modules", "Modullar soni", "Количество модулей", "Modules", T_INT, "", False, True, False, []),
        ("form_factor", "Format", "Форм-фактор", "Form Factor", T_SEL, "", False, True, False,
         [("dimm", "DIMM (PK)"), ("sodimm", "SODIMM (noutbuk)")]),
    ],
    "saqlash-qurilmalari": [
        ("capacity_gb", "Hajmi", "Объём", "Capacity", T_INT, "GB", True, True, True, []),
        ("drive_type", "Turi", "Тип", "Type", T_SEL, "", True, True, True,
         [("ssd_nvme", "SSD NVMe"), ("ssd_sata", "SSD SATA"), ("hdd", "HDD"), ("external", "Tashqi")]),
        ("interface", "Interfeys", "Интерфейс", "Interface", T_SEL, "", False, True, False,
         [("nvme_pcie4", "NVMe PCIe 4.0"), ("nvme_pcie3", "NVMe PCIe 3.0"),
          ("sata3", "SATA III"), ("usb_c", "USB-C")]),
        ("read_speed", "O'qish tezligi", "Скорость чтения", "Read Speed", T_INT, "MB/s", False, True, False, []),
        ("write_speed", "Yozish tezligi", "Скорость записи", "Write Speed", T_INT, "MB/s", False, False, False, []),
    ],
    "ona-platalar": [
        ("socket", "Soket", "Сокет", "Socket", T_TEXT, "", True, True, True, []),
        ("chipset", "Chipset", "Чипсет", "Chipset", T_TEXT, "", True, True, True, []),
        ("form_factor", "Format", "Форм-фактор", "Form Factor", T_SEL, "", True, True, False,
         [("atx", "ATX"), ("micro_atx", "Micro-ATX"), ("mini_itx", "Mini-ITX"), ("e_atx", "E-ATX")]),
        ("memory_type", "Xotira turi", "Тип памяти", "Memory Type", T_SEL, "", False, True, False,
         [("ddr4", "DDR4"), ("ddr5", "DDR5")]),
        ("memory_slots", "Xotira slotlari", "Слоты памяти", "Memory Slots", T_INT, "", False, False, False, []),
        ("m2_slots", "M.2 slotlari", "Слоты M.2", "M.2 Slots", T_INT, "", False, True, False, []),
    ],
    "quvvat-bloklari": [
        ("wattage", "Quvvati", "Мощность", "Wattage", T_INT, "W", True, True, True, []),
        ("certification", "Sertifikat", "Сертификат", "Certification", T_SEL, "", False, True, True,
         [("80_bronze", "80+ Bronze"), ("80_silver", "80+ Silver"), ("80_gold", "80+ Gold"),
          ("80_platinum", "80+ Platinum"), ("80_titanium", "80+ Titanium"), ("none", "Sertifikatsiz")]),
        ("modular", "Modulli", "Модульный", "Modular", T_SEL, "", False, True, False,
         [("full", "To'liq modulli"), ("semi", "Yarim modulli"), ("none", "Modulsiz")]),
    ],
    "klaviaturalar": [
        ("switch_type", "Switch turi", "Тип переключателей", "Switch Type", T_TEXT, "", False, True, True, []),
        ("layout", "Joylashuv", "Раскладка", "Layout", T_SEL, "", False, True, False,
         [("full", "To'liq (100%)"), ("tkl", "TKL (87%)"), ("75", "75%"), ("65", "65%"), ("60", "60%")]),
        ("connection", "Ulanish", "Подключение", "Connection", T_SEL, "", False, True, False,
         [("wired", "Simli"), ("wireless", "Simsiz"), ("both", "Ikkalasi")]),
        ("backlight", "Yoritish", "Подсветка", "Backlight", T_SEL, "", False, True, False,
         [("rgb", "RGB"), ("single", "Bir rangli"), ("none", "Yo'q")]),
    ],
    "sichqonchalar": [
        ("dpi", "Maksimal DPI", "Максимальный DPI", "Max DPI", T_INT, "", False, True, True, []),
        ("connection", "Ulanish", "Подключение", "Connection", T_SEL, "", False, True, False,
         [("wired", "Simli"), ("wireless", "Simsiz"), ("both", "Ikkalasi")]),
        ("buttons", "Tugmalar soni", "Количество кнопок", "Buttons", T_INT, "", False, False, False, []),
        ("weight_g", "Og'irligi", "Вес", "Weight", T_INT, "g", False, False, False, []),
    ],
    "quloqchinlar": [
        ("connection", "Ulanish", "Подключение", "Connection", T_SEL, "", False, True, True,
         [("wired_35", "3.5mm"), ("usb", "USB"), ("wireless", "Simsiz"), ("bluetooth", "Bluetooth")]),
        ("has_mic", "Mikrofon bor", "С микрофоном", "Microphone", T_BOOL, "", False, True, False, []),
        ("surround", "Surround ovoz", "Объёмный звук", "Surround", T_BOOL, "", False, False, False, []),
        ("noise_cancelling", "Shovqinni bostirish", "Шумоподавление", "ANC", T_BOOL, "", False, True, False, []),
    ],
    "printerlar": [
        ("print_type", "Bosib chiqarish turi", "Тип печати", "Print Type", T_SEL, "", True, True, True,
         [("laser", "Lazerli"), ("inkjet", "Siyohli"), ("thermal", "Termal")]),
        ("color", "Rangli bosib chiqarish", "Цветная печать", "Color", T_BOOL, "", False, True, True, []),
        ("functions", "Funksiyalar", "Функции", "Functions", T_TEXT, "", False, False, False, []),
        ("connection", "Ulanish", "Подключение", "Connection", T_TEXT, "", False, False, False, []),
    ],
    "tarmoq": [
        ("speed_mbps", "Tezligi", "Скорость", "Speed", T_INT, "Mbps", False, True, True, []),
        ("wifi_standard", "Wi-Fi standarti", "Стандарт Wi-Fi", "Wi-Fi Standard", T_SEL, "", False, True, False,
         [("wifi4", "Wi-Fi 4 (n)"), ("wifi5", "Wi-Fi 5 (ac)"),
          ("wifi6", "Wi-Fi 6 (ax)"), ("wifi6e", "Wi-Fi 6E"), ("wifi7", "Wi-Fi 7")]),
        ("ports", "Portlar soni", "Количество портов", "Ports", T_INT, "", False, False, False, []),
    ],
}

# Barcha kategoriyalarga tegadigan umumiy xususiyat — ildizga qo'yiladi
# va meros orqali hammaga tarqaladi.
COMMON_ATTRIBUTES = [
    ("warranty_months", "Kafolat muddati", "Гарантия", "Warranty", T_INT, "oy", False, True, False, []),
]
