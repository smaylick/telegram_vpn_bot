from app import storage
from app.config import BILLING_DAY


def build_welcome_text() -> str:
    price = storage.get_price()
    payment_info = storage.get_payment_info()
    return (
        "👋 <b>Вы подключились к нашему VPN-серверу</b>\n\n"
        f"• Оплата <b>каждый месяц {BILLING_DAY}-го</b> числа\n"
        f"• Сумма: <b>{price} ₽</b>\n"
        f"• Перевести: <b>{payment_info}</b>\n\n"
        "После перевода нажмите кнопку <b>«Оплачено ✅»</b> в напоминании.\n\n"
        "📖 Инструкции по подключению — в одноимённом разделе меню."
    )


def build_reminder_text() -> str:
    price = storage.get_price()
    payment_info = storage.get_payment_info()
    return (
        "👋 <b>Напоминание об оплате VPN</b>\n"
        f"Сумма: <b>{price} ₽</b>\n"
        f"Перевести: <b>{payment_info}</b>\n\n"
        "После перевода нажмите кнопку ↓"
    )


INFO_INTRO = (
    "🛡️ <b>Доступные способы подключения</b>\n\n"
    "Сейчас работают <b>2 сервера</b> (Астана и Германия) и <b>3 способа</b> подключения.\n"
    "Старые конфиги от прошлой инфраструктуры <b>больше не действуют</b>.\n\n"
    "• <b>AmneziaVPN X-Ray • Астана ⭐</b> — самый надёжный, рекомендуем в первую очередь.\n"
    "• <b>3X-UI X-Ray • Астана</b> — тот же X-Ray через панель, цепочка через Питер (Relay from SPB).\n"
    "• <b>AmneziaVPN AmneziaWG • Германия</b> — быстрый WireGuard, но нестабильный: IP могут блокировать.\n\n"
    "Выберите способ, чтобы получить подробную инструкцию ↓"
)


def _amnezia_xray_text(
    *,
    title: str,
    location: str,
    vpn_key: str,
    name_hint: str,
    extra_note: str = "",
) -> str:
    note_block = f"\n\n{extra_note}" if extra_note else ""
    return f"""<b>{title}</b>

<b>Что это за способ?</b>
Подключение через приложение <b>AmneziaVPN</b> по протоколу <b>X-Ray</b> к серверу в <b>{location}</b>. Трафик маскируется под обычный HTTPS.{note_block}

────────────────────────────────────────

<b>1. Установить AmneziaVPN</b>
Скачайте приложение для своей платформы: https://amnezia.org/ru/downloads

<b>2. Добавить администраторский профиль</b>
Скопируйте ключ ниже <b>целиком</b> и вставьте в приложение (➕ → «Вставить ключ»):

<code>{vpn_key}</code>

После вставки в приложении появится <b>администраторский профиль</b> сервера.

<b>3. Создать личное подключение (обязательно!)</b>
Админ-ключ — не для ежедневного использования. Через него выпускают личные ключи:
• Внизу экрана нажмите иконку «Поделиться».
• Создайте нового пользователя: имя, например, <code>{name_hint}</code>, протокол <b>X-Ray</b>, формат для AmneziaVPN.
• Скопируйте или сохраните ключ / QR — это ваш личный доступ.

<b>4. Добавить личное подключение</b>
• Снова ➕ → вставьте личный ключ → «Подключиться».
• Убедитесь, что соединение работает.

<b>5. Доступ родственникам</b>
На шаге 3 создайте отдельного пользователя с другим именем и отправьте им их ключ. Не пересылайте всем один ключ.

⚠️ <b>Не пересылайте</b> ключ из шага 2 посторонним — это администраторский доступ к серверу."""


def _amnezia_wg_text(
    *,
    title: str,
    location: str,
    vpn_key: str,
    name_hint: str,
    extra_note: str = "",
) -> str:
    note_block = f"\n\n{extra_note}" if extra_note else ""
    return f"""<b>{title}</b>

<b>Что это за способ?</b>
Подключение через приложение <b>AmneziaVPN</b> по протоколу <b>AmneziaWG</b> (усиленный WireGuard) к серверу в <b>{location}</b>.{note_block}

────────────────────────────────────────

<b>1. Установить AmneziaVPN</b>
Скачайте приложение для своей платформы: https://amnezia.org/ru/downloads

<b>2. Добавить администраторский профиль</b>
Скопируйте ключ ниже <b>целиком</b> и вставьте в приложение (➕ → «Вставить ключ»):

<code>{vpn_key}</code>

После вставки в приложении появится <b>администраторский профиль</b> сервера.

<b>3. Создать личное подключение (обязательно!)</b>
Админ-ключ — не для ежедневного использования. Через него выпускают личные ключи:
• Внизу экрана нажмите иконку «Поделиться».
• Создайте нового пользователя: имя, например, <code>{name_hint}</code>, протокол <b>AmneziaWG</b>, формат для AmneziaVPN.
• Скопируйте или сохраните ключ / QR — это ваш личный доступ.

<b>4. Добавить личное подключение</b>
• Снова ➕ → вставьте личный ключ → «Подключиться».
• Убедитесь, что соединение работает.

<b>5. Доступ родственникам</b>
На шаге 3 создайте отдельного пользователя с другим именем и отправьте им их ключ. Не пересылайте всем один ключ.

⚠️ <b>Не пересылайте</b> ключ из шага 2 посторонним — это администраторский доступ к серверу."""


INFO_AMNEZIA_XRAY_KZ = _amnezia_xray_text(
    title="🟣 AmneziaVPN • X-Ray • Астана ⭐",
    location="Астане (Казахстан)",
    vpn_key=(
        "vpn://AAABwXjahZBBTsMwEEX3OUXxGiLiFkS6BNawYoUQGiVGtdp6rJkJ0FZdwAk4Si_AHdIbYZukUiokZjWe__4f25tsFEpV6ASsM8RqOnpMs1ibQzekAqRg6czawtk7wUqdDsE0mx7Zk-KRJLonk_GRKclsxUR5TpZnkM_Xf0FC4DgGPXtCwchL5dUA3GbD7uk3R9XmBZqF3PzzksBxRdaLRReR9mv_sf9sd-13u-uRGbLcwTLdtyjLvLgqc31xnuvLnnBBvX81RLaujbtePXBaKNSYjvDA_IZUx4xbcHYBhR6f9P7us7Tuzk3w9xsJUVS2zX4A0nl1kw"
    ),
    name_hint="ivan_iphone_kz",
    extra_note=" Сейчас это <b>основной и самый стабильный</b> способ.",
)

INFO_WG_DE = _amnezia_wg_text(
    title="🟣 AmneziaVPN • AmneziaWG • Германия",
    location="Германии",
    vpn_key=(
        "vpn://AAAEX3jadZO_btswEMZ3P4WhtZXAP0eKKoIM6RAnQzuk7hIUBi3JjYBYFEgqSRsY6Bt06ItkKdCheQfljUrSslMD9AGCKH6_745HkY-TqYukVK2VTVtrk7ybXoc5H4_7UaDk_VcnH04GYYbdfAKcIcoZkBQLhokAKFjyNkITTxMkAGMgGFKCigIVnPA4TgOOcU65QCBSNxRAc-eN4rDFiaAAHLjDac5yzoWI4Rdh6Sd6Sk5PllP0IJhALvD4bIPzglNe8lXOOLgeKV_xCu25EqHyfw9GTLoXQMUEzWl-Gi0cdiGq0KMKHFXYMeWy9AqPSmv54EWG4mrTehVH1auwb0U071VojeGoFpqDeM7QHoaY1iltg5MhEU3caWVVqW4Xd-4UNyosPXpATL9sa7uQVaVrY7YdZiLDWXRNVsvW-OKLUMDjfdUlB-Dm0Pd6mzwt1239vZGpuzzk1bYJoy9bY1LVK9nf2vdHfXvOlLrp7Nje8Gv4_fJj-Ds8Dc_Dn5efO-xGGftBruvQWwEZxRnOWUYo3RGtUz-6jdJNVdXt2be5CUWt7uuR6KQx90pXPsdyfv5m_ikVs8-z8_Zul2P8I4SM373LsauqlbLJZDP5B7t36V8"
    ),
    name_hint="ivan_iphone_de",
    extra_note=(
        " На Германии сейчас только <b>AmneziaWG</b> (не X-Ray). Соединение <b>быстрое</b>, "
        "но <b>нестабильное</b>: иностранные IP могут блокировать — подходит, "
        "если нужен быстрый доступ «на свой страх и риск»."
    ),
)

INFO_XRAY_KZ = """<b>🔵 3X-UI • X-Ray • Астана</b>

<b>Что это за способ?</b>
Подключение по протоколу <b>X-Ray</b> (VLESS + Reality) через панель <b>3X-UI</b> на сервере в Астане. Трафик идёт по цепочке <b>через Санкт-Петербург</b> (входящее подключение <b>Relay from SPB</b>).

<b>Когда удобно</b>: если не хотите Amnezia, но нужен X-Ray через Астану. Стабильнее, чем выход в Германию, но <b>Amnezia X-Ray • Астана</b> по-прежнему рекомендуем в первую очередь.

────────────────────────────────────────

<b>Панель (выдача конфигов)</b>
• Адрес: https://199.189.250.26:31992/0W3PlCq7hF6SlaJdWJ/
• Логин: <code>3Xmv6qBjdW</code>
• Пароль: <code>80jjIza8xc</code>

Доступ только для своих; не публикуйте в открытых каналах.

────────────────────────────────────────

<b>Инструкция</b>

<b>1. Войти в панель</b>
• Откройте ссылку в браузере, введите логин и пароль.

<b>2. Добавить клиента</b>
• Перейдите в раздел <b>«Клиенты»</b>.
• Нажмите <b>«Добавить клиента»</b>.
• В поле <b>Email</b> — понятное имя, например: <code>[phone][android]ivan</code>.
• В <b>«Привязанный входящий»</b> выберите <b>Relay from SPB</b>.
• В поле <b>Flow</b> выберите <code>xtls-rprx-vision</code>.
• Сохраните.

<b>3. Получить QR или ссылку</b>
• В списке клиентов найдите свою запись.
• Нажмите на <b>QR-код</b> или скопируйте ссылку конфигурации.

<b>4. Подключиться в клиенте</b>
• Установите клиент с поддержкой X-Ray / VLESS / Reality, например:
  — Android — <b>v2rayNG</b>
  — iOS — v2ray, Shadowrocket
  — Windows — v2rayN
  — macOS / Linux — клиенты с VLESS/Reality
• Импортируйте конфиг (QR или ссылку) и включите VPN.

⚠️ <b>Важно</b>: не пересылайте QR и ссылку посторонним — по ним можно подключиться от вашего имени."""


INFO_TEXTS: dict[str, str] = {
    "amnezia_xray_kz": INFO_AMNEZIA_XRAY_KZ,
    "xray_kz": INFO_XRAY_KZ,
    "wg_de": INFO_WG_DE,
}

INFO_TITLES: dict[str, str] = {
    "amnezia_xray_kz": "AmneziaVPN • X-Ray • Астана",
    "xray_kz": "3X-UI • X-Ray • Астана",
    "wg_de": "AmneziaVPN • AmneziaWG • Германия",
}
