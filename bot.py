import json
import os
import uuid
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================================================
# SETTINGS
# =========================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

ADMIN_ID = 7864269692

QR_FILE = "qr.jpg"
DATA_FILE = "payments.json"


# =========================================================
# PLANS
# =========================================================

PLANS = {
    "plan_199": {
        "name": "1 Month",
        "price": 199,
        "days": 30,
    },

    "plan_299": {
        "name": "3 Months",
        "price": 299,
        "days": 90,
    },

    "plan_499": {
        "name": "Lifetime",
        "price": 499,
        "days": None,
    },
}


# =========================================================
# DATABASE
# =========================================================

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "payments": {},
            "users": {}
        }

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "payments" not in data:
            data["payments"] = {}

        if "users" not in data:
            data["users"] = {}

        return data

    except Exception:
        return {
            "payments": {},
            "users": {}
        }


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


# =========================================================
# HELPERS
# =========================================================

def create_order_id():
    return "ORD-" + uuid.uuid4().hex[:8].upper()


def current_time():
    return datetime.now().strftime("%d-%m-%Y %H:%M:%S")


def expiry_date(days):
    if days is None:
        return "Lifetime"

    return (
        datetime.now() + timedelta(days=days)
    ).strftime("%d-%m-%Y")


# =========================================================
# MAIN MENU
# =========================================================

def main_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "💎 View Plans",
                callback_data="show_plans"
            )
        ],

        [
            InlineKeyboardButton(
                "📊 My Status",
                callback_data="my_status"
            )
        ],

        [
            InlineKeyboardButton(
                "❓ Help",
                callback_data="help"
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# PLANS MENU
# =========================================================

def plans_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "💎 ₹199 — 1 Month",
                callback_data="plan_199"
            )
        ],

        [
            InlineKeyboardButton(
                "💎 ₹299 — 3 Months",
                callback_data="plan_299"
            )
        ],

        [
            InlineKeyboardButton(
                "💎 ₹499 — Lifetime",
                callback_data="plan_499"
            )
        ],

        [
            InlineKeyboardButton(
                "🏠 Main Menu",
                callback_data="back_home"
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# ADMIN PAYMENT BUTTONS
# =========================================================

def admin_payment_menu(order_id):

    keyboard = [

        [
            InlineKeyboardButton(
                "✅ APPROVE",
                callback_data=f"approve|{order_id}"
            ),

            InlineKeyboardButton(
                "❌ REJECT",
                callback_data=f"reject|{order_id}"
            ),
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    # Start par old rejected/current order ko force nahi karna
    # User fresh menu se new order bana sakta hai.

    await update.message.reply_text(

        "👋 Welcome to MyPayment!\n\n"
        "💎 Premium access lene ke liye "
        "neeche button par click karein.",

        reply_markup=main_menu()
    )


# =========================================================
# PLANS COMMAND
# =========================================================

async def plans_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "💎 PREMIUM PLANS\n\n"
        "🟢 ₹199 — 1 Month\n"
        "🟢 ₹299 — 3 Months\n"
        "🟢 ₹499 — Lifetime\n\n"
        "👇 Apna plan select karein:",

        reply_markup=plans_menu()
    )


# =========================================================
# HELP COMMAND
# =========================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "❓ HELP\n\n"

        "1️⃣ View Plans par click karein.\n"
        "2️⃣ Apna plan select karein.\n"
        "3️⃣ QR scan karke payment karein.\n"
        "4️⃣ Payment screenshot bhejein.\n"
        "5️⃣ Admin payment verify karega.\n\n"

        "Payment approve hone ke baad "
        "premium access mil jayega.\n\n"

        "Commands:\n"
        "/start - Main Menu\n"
        "/plans - Plans\n"
        "/status - Payment Status\n"
        "/help - Help\n"
        "/history - Admin Payment History"

    )


# =========================================================
# STATUS COMMAND
# =========================================================

async def status_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = str(update.effective_user.id)

    data = load_data()

    payments = []

    for payment in data["payments"].values():

        if str(payment.get("user_id")) == user_id:
            payments.append(payment)

    if not payments:

        await update.message.reply_text(

            "📊 PAYMENT STATUS\n\n"
            "❌ Abhi koi payment nahi mili.\n\n"
            "💎 Plan select karein:",

            reply_markup=plans_menu()
        )

        return

    payments.sort(
        key=lambda x: x.get("created_at", ""),
        reverse=True
    )

    payment = payments[0]

    status = payment.get("status", "pending")


    # APPROVED
    if status == "approved":

        await update.message.reply_text(

            "📊 PAYMENT STATUS\n\n"

            "✅ APPROVED\n\n"

            f"🆔 Order ID: {payment['order_id']}\n"
            f"💎 Plan: {payment['plan']}\n"
            f"💰 Amount: ₹{payment['amount']}\n"
            f"📅 Expiry: {payment['expiry']}\n\n"

            "🎉 Premium payment successfully verified.",

            reply_markup=main_menu()
        )

        return


    # REJECTED
    if status == "rejected":

        await update.message.reply_text(

            "📊 PAYMENT STATUS\n\n"

            "❌ PAYMENT REJECTED\n\n"

            f"🆔 Order ID: {payment['order_id']}\n\n"

            "Aap dobara payment kar sakte hain.\n"
            "👇 Neeche se plan select karein:",

            reply_markup=plans_menu()
        )

        return


    # PENDING
    await update.message.reply_text(

        "📊 PAYMENT STATUS\n\n"

        "⏳ PAYMENT UNDER REVIEW\n\n"

        f"🆔 Order ID: {payment['order_id']}\n"
        f"💎 Plan: {payment['plan']}\n"
        f"💰 Amount: ₹{payment['amount']}\n\n"

        "Admin payment verify kar raha hai."

    )


# =========================================================
# SHOW PLANS
# =========================================================

async def show_plans(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = (

        "💎 PREMIUM PLANS\n\n"

        "🟢 ₹199 — 1 Month\n"
        "🟢 ₹299 — 3 Months\n"
        "🟢 ₹499 — Lifetime\n\n"

        "👇 Apna plan select karein:"
    )

    query = update.callback_query

    if query:

        await query.edit_message_text(
            message,
            reply_markup=plans_menu()
        )

    else:

        await update.message.reply_text(
            message,
            reply_markup=plans_menu()
        )


# =========================================================
# PLAN SELECTED
# =========================================================

async def plan_selected(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    plan_key = query.data

    if plan_key not in PLANS:
        return

    plan = PLANS[plan_key]

    user = update.effective_user

    user_id = user.id

    data = load_data()


    # =====================================================
    # ALWAYS CREATE COMPLETELY NEW ORDER
    # =====================================================

    order_id = create_order_id()


    payment = {

        "order_id": order_id,

        "user_id": user_id,

        "username": user.username or "None",

        "name": user.first_name or "Unknown",

        "plan": plan["name"],

        "amount": plan["price"],

        "days": plan["days"],

        "status": "waiting_screenshot",

        "created_at": current_time(),

        "expiry": None,

        "screenshot_id": None,

        "screenshot_time": None,

        "approved_at": None,

        "rejected_at": None,

    }


    data["payments"][order_id] = payment

    save_data(data)


    # IMPORTANT:
    # Every plan selection replaces old order.
    context.user_data["current_order"] = order_id


    # =====================================================
    # QR CHECK
    # =====================================================

    if not os.path.exists(QR_FILE):

        await query.message.reply_text(

            "❌ QR file nahi mili.\n\n"

            "Bot folder ke andar "
            "`qr.jpg` file honi chahiye.\n\n"

            "Expected location:\n"
            "telegrampaymentbot\\qr.jpg"

        )

        return


    # =====================================================
    # PAYMENT MESSAGE
    # =====================================================

    caption = (

        "💎 PREMIUM PAYMENT\n\n"

        f"📦 Plan: {plan['name']}\n"
        f"💰 Amount: ₹{plan['price']}\n"
        f"🆔 Order ID: {order_id}\n\n"

        "📱 QR code scan karke payment karein.\n\n"

        "📸 Payment complete hone ke baad "
        "payment ka screenshot isi chat mein bhejein.\n\n"

        "⚠️ Har payment ke liye naya Order ID generate hota hai."

    )


    with open(QR_FILE, "rb") as qr:

        await query.message.reply_photo(

            photo=qr,

            caption=caption

        )


# =========================================================
# SCREENSHOT RECEIVED
# =========================================================

async def screenshot_received(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    # Current active order
    order_id = context.user_data.get("current_order")


    # =====================================================
    # NO ORDER
    # =====================================================

    if not order_id:

        await update.message.reply_text(

            "⚠️ Pehle plan select karein.\n\n"
            "👇 Plans:",

            reply_markup=plans_menu()
        )

        return


    data = load_data()

    payment = data["payments"].get(order_id)


    # =====================================================
    # ORDER NOT FOUND
    # =====================================================

    if not payment:

        # Clear broken order
        context.user_data.pop("current_order", None)

        await update.message.reply_text(

            "❌ Order nahi mila.\n\n"
            "Please dobara plan select karein.",

            reply_markup=plans_menu()
        )

        return


    # =====================================================
    # ONLY ACCEPT ACTIVE PAYMENT
    # =====================================================

    if payment["status"] not in [
        "waiting_screenshot",
        "pending"
    ]:

        # IMPORTANT:
        # Rejected/approved order screenshot cannot be reused.
        # User gets NEW PLAN button.

        await update.message.reply_text(

            "⚠️ Ye order already process ho chuka hai.\n\n"
            "👇 Naya payment order banane ke liye "
            "plan select karein:",

            reply_markup=plans_menu()
        )

        return


    # =====================================================
    # DUPLICATE SCREENSHOT
    # =====================================================

    if payment.get("screenshot_id"):

        await update.message.reply_text(

            "⚠️ Is Order ID ka screenshot already receive "
            "ho chuka hai.\n\n"

            f"🆔 Order ID: {order_id}\n\n"

            "Admin verification ka wait karein."

        )

        return


    # =====================================================
    # SAVE SCREENSHOT
    # =====================================================

    photo = update.message.photo[-1]

    payment["screenshot_id"] = photo.file_id

    payment["status"] = "pending"

    payment["screenshot_time"] = current_time()

    save_data(data)


    # =====================================================
    # SEND TO ADMIN
    # =====================================================

    admin_caption = (

        "💰 NEW PAYMENT SCREENSHOT\n\n"

        f"🆔 Order ID: {order_id}\n"

        f"👤 Name: {user.first_name}\n"

        f"🔹 Username: "
        f"@{user.username if user.username else 'None'}\n"

        f"🔢 Telegram ID: {user.id}\n"

        f"💎 Plan: {payment['plan']}\n"

        f"💰 Amount: ₹{payment['amount']}\n"

        f"🕐 Time: {payment['screenshot_time']}\n\n"

        "👇 Payment verify karein:"
    )


    await context.bot.send_photo(

        chat_id=ADMIN_ID,

        photo=photo.file_id,

        caption=admin_caption,

        reply_markup=admin_payment_menu(order_id)

    )


    # =====================================================
    # USER MESSAGE
    # =====================================================

    await update.message.reply_text(

        "✅ Payment screenshot receive ho gaya.\n\n"

        f"🆔 Order ID: {order_id}\n\n"

        "⏳ Admin payment verify karega.\n"

        "Verification ke baad result automatically "
        "aapko mil jayega."

    )


# =========================================================
# ADMIN APPROVE / REJECT
# =========================================================

async def admin_action(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query


    # =====================================================
    # ADMIN SECURITY
    # =====================================================

    if query.from_user.id != ADMIN_ID:

        await query.answer(

            "❌ You are not authorized.",

            show_alert=True

        )

        return


    await query.answer()


    parts = query.data.split("|", 1)


    if len(parts) != 2:
        return


    action = parts[0]

    order_id = parts[1]


    data = load_data()

    payment = data["payments"].get(order_id)


    if not payment:

        await query.message.reply_text(

            "❌ Payment record not found."

        )

        return


    user_id = payment["user_id"]


    # =====================================================
    # APPROVE
    # =====================================================

    if action == "approve":

        if payment["status"] == "approved":

            await query.answer(

                "Already approved.",

                show_alert=True

            )

            return


        if payment["status"] == "rejected":

            await query.answer(

                "Already rejected.",

                show_alert=True

            )

            return


        payment["status"] = "approved"

        payment["approved_at"] = current_time()


        if payment["days"] is None:

            payment["expiry"] = "Lifetime"

        else:

            payment["expiry"] = expiry_date(
                payment["days"]
            )


        save_data(data)


        # =================================================
        # UPDATE ADMIN MESSAGE
        # =================================================

        try:

            await query.edit_message_caption(

                caption=(

                    "✅ PAYMENT APPROVED\n\n"

                    f"🆔 Order ID: {order_id}\n"

                    f"👤 Name: {payment['name']}\n"

                    f"💎 Plan: {payment['plan']}\n"

                    f"💰 Amount: ₹{payment['amount']}\n"

                    f"📅 Expiry: {payment['expiry']}\n"

                    f"🕐 Approved: "
                    f"{payment['approved_at']}"

                ),

                reply_markup=None

            )

        except Exception:

            pass


        # =================================================
        # SEND USER RECEIPT
        # =================================================

        receipt = (

            "🎉 PAYMENT APPROVED!\n\n"

            "💎 Your Premium access has been approved.\n\n"

            f"🧾 Order ID: {order_id}\n"

            f"📦 Plan: {payment['plan']}\n"

            f"💰 Amount: ₹{payment['amount']}\n"

            f"📅 Expiry: {payment['expiry']}\n\n"

            "✅ Payment successfully verified.\n\n"

            "Thank you for your purchase! ❤️"

        )


        try:

            await context.bot.send_message(

                chat_id=user_id,

                text=receipt,

                reply_markup=main_menu()

            )

        except Exception:

            await query.message.reply_text(

                "⚠️ Payment approved, "
                "but user ko message nahi bhej saka."

            )

        return


    # =====================================================
    # REJECT
    # =====================================================

    if action == "reject":

        if payment["status"] == "approved":

            await query.answer(

                "Already approved.",

                show_alert=True

            )

            return


        if payment["status"] == "rejected":

            await query.answer(

                "Already rejected.",

                show_alert=True

            )

            return


        payment["status"] = "rejected"

        payment["rejected_at"] = current_time()


        save_data(data)


        # =================================================
        # VERY IMPORTANT FIX
        # Clear old rejected order from user's session.
        # =================================================

        if context.user_data.get("current_order") == order_id:

            context.user_data.pop(
                "current_order",
                None
            )


        # =================================================
        # UPDATE ADMIN MESSAGE
        # =================================================

        try:

            await query.edit_message_caption(

                caption=(

                    "❌ PAYMENT REJECTED\n\n"

                    f"🆔 Order ID: {order_id}\n"

                    f"👤 Name: {payment['name']}\n"

                    f"💎 Plan: {payment['plan']}\n"

                    f"💰 Amount: ₹{payment['amount']}\n"

                    f"🕐 Rejected: "
                    f"{payment['rejected_at']}"

                ),

                reply_markup=None

            )

        except Exception:

            pass


        # =================================================
        # SEND REJECTION + NEW PLAN BUTTONS
        # =================================================

        try:

            await context.bot.send_message(

                chat_id=user_id,

                text=(

                    "❌ PAYMENT REJECTED\n\n"

                    f"🧾 Old Order ID: {order_id}\n\n"

                    "Aapka payment screenshot "
                    "verify nahi ho saka.\n\n"

                    "⚠️ Koi problem nahi — aap "
                    "dobara payment kar sakte hain.\n\n"

                    "👇 Neeche se plan select karein. "
                    "Aapko NEW Order ID milega."

                ),

                reply_markup=plans_menu()

            )

        except Exception:

            await query.message.reply_text(

                "⚠️ Rejected, but user ko message "
                "nahi bhej saka."

            )

        return


# =========================================================
# ADMIN HISTORY
# =========================================================

async def history_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if update.effective_user.id != ADMIN_ID:

        await update.message.reply_text(

            "❌ You are not authorized."

        )

        return


    data = load_data()

    payments = list(
        data["payments"].values()
    )


    if not payments:

        await update.message.reply_text(

            "📋 Payment history empty hai."

        )

        return


    payments.sort(

        key=lambda x: x.get(
            "created_at",
            ""
        ),

        reverse=True

    )


    text = "📋 PAYMENT HISTORY\n\n"


    for payment in payments[:30]:

        text += (

            f"🆔 {payment.get('order_id')}\n"

            f"👤 {payment.get('name')}\n"

            f"💎 {payment.get('plan')}\n"

            f"💰 ₹{payment.get('amount')}\n"

            f"📌 {payment.get('status')}\n"

            f"🕐 {payment.get('created_at')}\n\n"

        )


    await update.message.reply_text(text)


# =========================================================
# BUTTON HANDLER
# =========================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    data = query.data


    # =====================================================
    # ADMIN
    # =====================================================

    if (
        data.startswith("approve|")
        or
        data.startswith("reject|")
    ):

        await admin_action(
            update,
            context
        )

        return


    # =====================================================
    # SHOW PLANS
    # =====================================================

    if data == "show_plans":

        await query.answer()

        await show_plans(
            update,
            context
        )

        return


    # =====================================================
    # PLAN
    # =====================================================

    if data in PLANS:

        await plan_selected(
            update,
            context
        )

        return


    # =====================================================
    # BACK HOME
    # =====================================================

    if data == "back_home":

        await query.answer()

        await query.edit_message_text(

            "👋 Welcome to MyPayment!\n\n"

            "💎 Premium access lene ke liye "
            "neeche button par click karein.",

            reply_markup=main_menu()

        )

        return


    # =====================================================
    # STATUS
    # =====================================================

    if data == "my_status":

        await query.answer()


        user_id = str(
            query.from_user.id
        )


        db = load_data()


        payments = [

            p for p in db["payments"].values()

            if str(
                p.get("user_id")
            ) == user_id

        ]


        if not payments:

            await query.edit_message_text(

                "📊 PAYMENT STATUS\n\n"

                "❌ Abhi koi payment nahi mili.\n\n"

                "👇 Plan select karein:",

                reply_markup=plans_menu()

            )

            return


        payments.sort(

            key=lambda x: x.get(
                "created_at",
                ""
            ),

            reverse=True

        )


        payment = payments[0]


        if payment["status"] == "approved":

            text = (

                "📊 PAYMENT STATUS\n\n"

                "✅ APPROVED\n\n"

                f"🆔 Order ID: "
                f"{payment['order_id']}\n"

                f"💎 Plan: "
                f"{payment['plan']}\n"

                f"💰 Amount: "
                f"₹{payment['amount']}\n"

                f"📅 Expiry: "
                f"{payment['expiry']}"

            )

            keyboard = main_menu()


        elif payment["status"] == "rejected":

            text = (

                "📊 PAYMENT STATUS\n\n"

                "❌ PAYMENT REJECTED\n\n"

                f"🆔 Old Order ID: "
                f"{payment['order_id']}\n\n"

                "Aap dobara payment kar sakte hain.\n\n"

                "👇 Naya plan select karein:"

            )

            keyboard = plans_menu()


        else:

            text = (

                "📊 PAYMENT STATUS\n\n"

                "⏳ UNDER REVIEW\n\n"

                f"🆔 Order ID: "
                f"{payment['order_id']}\n"

                f"💎 Plan: "
                f"{payment['plan']}\n"

                f"💰 Amount: "
                f"₹{payment['amount']}\n\n"

                "Admin payment verify kar raha hai."

            )

            keyboard = main_menu()


        await query.edit_message_text(

            text,

            reply_markup=keyboard

        )

        return


    # =====================================================
    # HELP
    # =====================================================

    if data == "help":

        await query.answer()

        await query.edit_message_text(

            "❓ HELP\n\n"

            "💎 Plan select karein.\n"
            "📱 QR scan karke payment karein.\n"
            "📸 Screenshot bhejein.\n"
            "⏳ Admin verification ka wait karein.\n\n"

            "/start - Main Menu\n"
            "/plans - Plans\n"
            "/status - Status\n"
            "/help - Help",

            reply_markup=main_menu()

        )

        return


# =========================================================
# ERROR HANDLER
# =========================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    print(
        "ERROR:",
        context.error
    )


# =========================================================
# MAIN
# =========================================================

def main():

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )


    # Commands

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "plans",
            plans_command
        )
    )

    app.add_handler(
        CommandHandler(
            "help",
            help_command
        )
    )

    app.add_handler(
        CommandHandler(
            "status",
            status_command
        )
    )

    app.add_handler(
        CommandHandler(
            "history",
            history_command
        )
    )


    # All buttons

    app.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )


    # Payment screenshots

    app.add_handler(
        MessageHandler(
            filters.PHOTO,
            screenshot_received
        )
    )


    # Error handler

    app.add_error_handler(
        error_handler
    )


    print(
        "================================"
    )

    print(
        "     MyPayment Bot is running..."
    )

    print(
        "================================"
    )


    app.run_polling()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()
