import os
import asyncio
import aiosqlite
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

import discord
from discord.ext import commands
from discord import app_commands

load_dotenv()

TOKEN = os.getenv('TOKEN')
ADMIN_CHANNEL_ID = int(os.getenv("ADMIN_CHANNEL_ID") or 0)
DB_PATH = os.getenv("DB_PATH", "orders.db")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)


def get_msk_time():
    msk_tz = timezone(timedelta(hours=3))
    return datetime.now(msk_tz)

FAQ_ANSWERS = {}

FAQ_ANSWERS["pricing"] = discord.Embed(
    title="🤖 Прайс-лист на разработку Discord-ботов",
    description="Выбери пакет и ознакомься, что входит в каждый уровень разработки. Поддержка обязательна и оплачивается ежемесячно.",
    color=discord.Color.gold()
)

# Lite
FAQ_ANSWERS["pricing"].add_field(
    name="1️⃣ Lite — базовый бот",
    value=(
        "• Минимальный бот с базовой функциональностью для сервера\n"
        "• Примеры функций:\n"
        "   - Прием заявок (например, в семью)\n"
        "   - Авто-приветствие новых участников\n"
        "   - Простые уведомления в канал или ЛС\n"
        "   - Базовые команды управления ролями\n"
        "• Функции могут быть добавлены или убраны по согласованию\n"
        "⏱ Срок: 2–4 дня\n"
        "💲 Цена создания: от $20\n"
        "💲 Поддержка: $8/мес (включая хостинг)"
    ),
    inline=False
)

# Medium
FAQ_ANSWERS["pricing"].add_field(
    name="2️⃣ Medium — новые функции и интеграции",
    value=(
        "• Добавление новых команд и функций в существующий бот\n"
        "• Интеграции с внешними сервисами (Google Calendar, Twitch, REST API)\n"
        "• Логика уведомлений, простые базы данных\n"
        "• Частичная кастомизация интерфейса и embed’ов\n"
        "⏱ Срок: 3–7 дней (в зависимости от сложности)\n"
        "💲 Цена создания: от $50–$75\n"
        "💲 Поддержка: $15/мес (включая хостинг)"
    ),
    inline=False
)

# Pro
FAQ_ANSWERS["pricing"].add_field(
    name="3️⃣ Pro — бот с нуля под ваш запрос",
    value=(
        "• Полностью новый бот с нуля\n"
        "• Все команды, интеграции, базы данных и логика\n"
        "• Настройка интерфейса, embed’ов, Views, модальных окон\n"
        "• Поддержка и хостинг после передачи\n"
        "⏱ Срок: 1–3 недели (в зависимости от объема проекта)\n"
        "💲 Цена создания: от $100–$150\n"
        "💲 Поддержка: $25/мес (включая хостинг)"
    ),
    inline=False
)

# Пример расчета
FAQ_ANSWERS["pricing"].add_field(
    name="💡 Пример расчёта",
    value=(
        "Клиент выбирает пакет Medium — новые функции и интеграции:\n"
        "Создание бота: $50–$75\n"
        "Поддержка каждый месяц: $15/мес (включая хостинг)"
    ),
    inline=False
)

FAQ_ANSWERS["ordering"] = discord.Embed(
    title="📝 Как оформить заказ?",
    description=(
        "1. Нажмите кнопку `Оформить заказ`.\n"
        "2. Заполните форму с описанием задачи, бюджета и сроков.\n"
        "3. После отправки я свяжусь с вами в ЛС для уточнения деталей."
    ),
    color=discord.Color.blue()
)

FAQ_ANSWERS["turnkey"] = discord.Embed(
    title="🔑 Что значит «под ключ»?",
    description=(
        "Под ключ означает, что бот создается полностью с нуля по вашему запросу.\n"
        "Вы получаете готового к использованию бота, все функции и интеграции.\n"
        "Поддержка включена обязательно, чтобы бот работал стабильно на хосте."
    ),
    color=discord.Color.blue()
)

FAQ_ANSWERS["support"] = discord.Embed(
    title="⚙️ Поддержка бота",
    description=(
        "Поддержка — обязательна для всех пакетов.\n"
        "Что включено:\n"
        "• Мониторинг работоспособности\n"
        "• Исправление ошибок и багов\n"
        "• Обновление функций\n"
        "Цена зависит от пакета: Lite — $8/мес, Medium — $15/мес, Pro — $25/мес"
    ),
    color=discord.Color.blue()
)

FAQ_ANSWERS["changes"] = discord.Embed(
    title="✏️ Изменение функционала",
    description=(
        "Вы можете вносить изменения или добавлять функции после создания бота.\n"
        "Изменения оформляются как новые задачи и добавляют к стоимости пакета или входят в поддержку."
    ),
    color=discord.Color.blue()
)

FAQ_ANSWERS["delivery"] = discord.Embed(
    title="⏱ Сроки выполнения",
    description=(
        "• Lite: 2–4 дня\n"
        "• Medium: 3–7 дней\n"
        "• Pro: 1–3 недели (в зависимости от объема и сложности проекта)"
    ),
    color=discord.Color.blue()
)

class FaqSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Цены и пакеты", value="pricing"),
            discord.SelectOption(label="Как оформить заказ?", value="ordering"),
            discord.SelectOption(label="Что такое 'под ключ'?", value="turnkey"),
            discord.SelectOption(label="Поддержка бота", value="support"),
            discord.SelectOption(label="Можно ли изменить функционал?", value="changes"),
            discord.SelectOption(label="Сроки выполнения", value="delivery"),
        ]
        super().__init__(placeholder="Выберите вопрос...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        embed = FAQ_ANSWERS.get(self.values[0])
        if embed:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("❌ Ответ на этот вопрос не найден.", ephemeral=True)

class FaqView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(FaqSelect())

# ------------------ DB HELPERS ------------------
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                description TEXT,
                budget TEXT,
                deadline TEXT,
                created_at TEXT
            )
            """
        )
        await db.commit()

async def save_order(user: discord.User, description: str, budget: str, deadline: str) -> int:
    created_at = get_msk_time().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO orders (user_id, username, description, budget, deadline, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user.id, f"{user.name}#{user.discriminator}", description, budget, deadline, created_at)
        )
        await db.commit()
        order_id = cursor.lastrowid
        await cursor.close()
    return order_id

async def fetch_recent_orders(limit: int = 10):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id, user_id, username, description, budget, deadline, created_at FROM orders ORDER BY id DESC LIMIT ?", (limit,))
        rows = await cursor.fetchall()
        await cursor.close()
    return rows

# ------------------ Modal ------------------
class OrderModal(discord.ui.Modal, title="Оформление заказа"):
    description = discord.ui.TextInput(
        label="Краткое описание (что нужно сделать)",
        style=discord.TextStyle.long,
        placeholder="Опиши, что должен уметь бот, какие команды и интеграции...",
        required=True,
        max_length=2000
    )
    budget = discord.ui.TextInput(
        label="Бюджет (USD, опционально)",
        style=discord.TextStyle.short,
        required=False,
        placeholder="Например: 30"
    )
    deadline = discord.ui.TextInput(
        label="Желаемый срок (опционально)",
        style=discord.TextStyle.short,
        required=False,
        placeholder="Например: 7 дней"
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        user = interaction.user
        desc = self.description.value.strip()
        budget = self.budget.value.strip() if self.budget.value else "Не указан"
        deadline = self.deadline.value.strip() if self.deadline.value else "Не указан"

        try:
            if budget != "Не указан":
                b = float(budget.replace('$', '').strip())
                budget = f"${int(b) if b.is_integer() else b}"
        except Exception:
            pass

        try:
            order_id = await save_order(user, desc, budget, deadline)
        except Exception as e:
            await interaction.followup.send("Произошла ошибка при сохранении в базу.", ephemeral=True)
            print("DB save error:", e)
            return

        await interaction.followup.send(embed=discord.Embed(
            title=f"Заявка #{order_id} получена",
            description=("Спасибо! Твоя заявка принята.\n" "Я свяжусь с тобой в ЛС для уточнения деталей."),
            color=discord.Color.green()
        ), ephemeral=True)

        if ADMIN_CHANNEL_ID:
            bot.loop.create_task(notify_admins(order_id, user, desc, budget, deadline))

# ------------------ Views ------------------
class InfoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(discord.ui.Button(
                label="💬 Написать в ЛС", 
                style=discord.ButtonStyle.link, 
                url="https://discord.com/users/515859274723885088"
            ))

    @discord.ui.button(label="💸 Оформить заказ", style=discord.ButtonStyle.success)
    async def order_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(OrderModal())

    @discord.ui.button(label="❓ Частые вопросы", style=discord.ButtonStyle.primary)
    async def faq_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Выберите вопрос из списка ниже:", view=FaqView(), ephemeral=True)

# ------------------ Notify admins ------------------
async def notify_admins(order_id: int, user: discord.User, desc: str, budget: str, deadline: str):
    await bot.wait_until_ready()
    try:
        channel = bot.get_channel(ADMIN_CHANNEL_ID) or await bot.fetch_channel(ADMIN_CHANNEL_ID)
    except Exception as e:
        print("Не удалось найти админ-канал:", e)
        channel = None

    if not channel:
        print("ADMIN_CHANNEL_ID не настроен или указан неверно.")
        return

    embed = discord.Embed(title=f"Новая заявка #{order_id}", color=discord.Color.orange())
    embed.add_field(name="Клиент", value=f"{user} (`{user.id}`)", inline=False)
    embed.add_field(name="Краткое описание", value=(desc[:1024] + "..." if len(desc) > 1024 else desc), inline=False)

    embed.add_field(name="Бюджет", value=budget or '—', inline=True)
    embed.add_field(name="Срок", value=deadline or '—', inline=True)

    embed.set_footer(text=f"Заявка #{order_id} • {get_msk_time().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        msg = await channel.send(embed=embed)
        try:
            await msg.add_reaction("📌")
        except Exception:
            pass
    except Exception as e:
        print("Ошибка отправки уведомления в админ-канал:", e)

# ------------------ Команды ------------------
@bot.tree.command(name="info", description="Узнать цены и посмотреть портфолио")
async def info(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Профессиональная разработка Discord-ботов",
        description="Привет! Выбери действие ниже или оформи заказ прямо из диалога.",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="💳 Прайс-лист",
        value=(
            "• **Lite** — базовый бот для вашего сервера: **от $20**\n"
            "• **Medium** — новые функции, интеграции: **от $50**\n"
            "• **Pro** — бот с нуля под Ваш запрос, под ключ: **от $100**\n"
            "• **Поддержка бота**: $25/мес"
        ),
        inline=False
    )

    embed.add_field(
        name="📂 Реализованные системы (пример)",
        value=(
            "• Системы верификации и приватные заявки (Modals + Views)\n"
            "• Интеграции: Google Calendar, OAuth2, Twitch, внешние REST API\n"
            "• Авто-уведомления, расписания и tasks.loop\n"
            "• CRM-подобная логика: заявки, KPI, рейтинги, архивы\n"
            "• Persistent Views и self-healing UI\n"
            "• SQLite / UPSERT / сложные схемы БД"
        ),
        inline=False
    )

    embed.add_field(name="📞 Контакты", value="Напиши в ЛС или нажми кнопку `Оформить заказ` — и опиши задачу.", inline=False)
    embed.set_footer(text="Готово к работе — отвечаю в ЛС и по заявкам в админ-канале")

    await interaction.response.send_message(embed=embed, view=InfoView(), ephemeral=True)

@bot.tree.command(name="reply", description="Ответить клиенту по ID")
@app_commands.describe(user_id="ID пользователя", message="Текст ответа")
async def reply_slash(interaction: discord.Interaction, user_id: str, message: str):
    perms = interaction.user.guild_permissions if interaction.guild else None
    is_owner = await bot.is_owner(interaction.user)
    if not (is_owner or (perms and perms.manage_guild)):
        await interaction.response.send_message("У тебя нет прав для этой команды.", ephemeral=True)
        return
    try:
        user = await bot.fetch_user(int(user_id))
    except Exception:
        return await interaction.response.send_message('Не удалось найти пользователя по ID.', ephemeral=True)

    try:
        await user.send(embed=discord.Embed(
            title="📩 Ответ по твоей заявке",
            description=message,
            color=discord.Color.green()
        ))
        await interaction.response.send_message("Отправлено!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Не удалось отправить сообщение: {e}", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    await init_db()
    try:
        await bot.tree.sync()
    except Exception as e:
        print("Error syncing commands:", e)

if __name__ == "__main__":
    bot.run(TOKEN)
