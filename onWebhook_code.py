# ================= VALIDATION =================
if options is None:

    raise ReturnCommand()


if options.json is None:

    raise ReturnCommand()


# ================= RESPONSE =================
res = options.json

status = str(
    res.get("status", "")
).lower().strip()

message_txt = str(
    res.get("message", "")
).strip()

# Device fingerprint sent by the verification page. This is the SAME
# value regardless of whether the user opened the link in real Telegram
# or a clone app (Nicegram, Nekogram, etc.) — it's computed from the
# physical device's screen/timezone/cores/UA, not from app-local storage.
fp = str(
    res.get("fp", "")
).strip()

device_check_enabled = bool(
    res.get("deviceCheckEnabled", True)
)


# ================= VERIFIED =================
if (
    status == "pass"
    and message_txt == "Verified Successfully"
):

    # ================= GLOBAL SAME-DEVICE CHECK (server-side) =================
    # This replaces the old client-side localStorage check, which silently
    # failed to catch repeat devices across Telegram vs clone apps because
    # each app's WebView has its own isolated localStorage.
    #
    # FpOwners is a single bot-wide dict: { fingerprint: first_user_id }
    # Since this lives in Bot.getData(), it is shared across every user,
    # every account, and every Telegram client (official or clone) — so a
    # device that verified once in real Telegram and again in a clone will
    # now correctly be caught here.
    is_same_device = False

    if device_check_enabled and fp:

        FpOwners = Bot.getData("FpOwners") or {}

        owner = FpOwners.get(fp)

        if owner is None:
            # First time this physical device has verified — claim it
            FpOwners[fp] = str(u)
            Bot.saveData("FpOwners", FpOwners)

        elif owner != str(u):
            # This fingerprint already belongs to a different user —
            # same physical device, different Telegram account (or same
            # account through a clone app after verifying in real Telegram).
            is_same_device = True

        # else: owner == str(u) -> this user re-verifying on their own
        # device, not a same-device case.

    if is_same_device:

        Bot.saveData(
            str(u) + "sameDev",
            "yes"
        )

        User.saveData(
            "verify",
            "ok"
        )

        User.saveData(
            "PhVerification",
            "Verified"
        )

        # ================= SAME DEVICE SAFE REFERRAL =================
        dn = User.getData("dn") or "n"

        if dn == "n":

            refBy = Bot.getData(
                str(u) + "Referral"
            ) or "NONE"

            if refBy != "NONE" and refBy != str(u):

                joinedSame = User.getData(
                    "joined_same_ref"
                )

                if not joinedSame:

                    RefSameDevC = Bot.getData(
                        str(refBy) + "RefSameDevC"
                    ) or 0

                    Bot.saveData(
                        str(refBy) + "RefSameDevC",
                        RefSameDevC + 1
                    )

                    User.saveData(
                        "joined_same_ref",
                        refBy
                    )

            User.saveData(
                "dn",
                "y"
            )

        Bot.runCommand(
            "/PIRO_MainMenu",
            options="""
<b>⚠️ Same Device Detected

🎁 Referral Bonus Not Available.

🥳 But You Can Still Use The Bot.</b>
"""
        )

        raise ReturnCommand()

    # ================= NORMAL VERIFIED (not same device) =================
    User.saveData(
        "verify",
        "ok"
    )

    User.saveData(
        "PhVerification",
        "Verified"
    )

    # ================= SAFE REFERRAL =================
    dn = User.getData("dn") or "n"

    if dn == "n":

        refBy = Bot.getData(
            str(u) + "Referral"
        ) or "NONE"

        # Prevent self referral
        if refBy != "NONE" and refBy != str(u):

            # Prevent double referral
            joined = User.getData(
                "joined_ref"
            )

            if not joined:

                RefJC = Bot.getData(
                    str(refBy) + "RefJC"
                ) or 0

                Bot.saveData(
                    str(refBy) + "RefJC",
                    RefJC + 1
                )

                User.saveData(
                    "joined_ref",
                    refBy
                )

        User.saveData(
            "dn",
            "y"
        )

    bot.sendMessage(
        """
<b>🎉 Verification Successful!

✅ Welcome To Wallet Bot.</b>
""",
        parse_mode="HTML"
    )

    Bot.runCommand(
        "/PIRO_MainMenu"
    )

    raise ReturnCommand()


# ================= ALREADY VERIFIED =================
elif (
    status == "pass"
    and message_txt == "Already Verified"
):

    User.saveData(
        "verify",
        "ok"
    )

    User.saveData(
        "PhVerification",
        "Verified"
    )

    Bot.runCommand(
        "/PIRO_MainMenu"
    )

    raise ReturnCommand()


# ================= VPN DETECTED =================
elif (
    status == "fail"
    and "VPN" in message_txt
):

    bot.sendMessage(
        """
<b>🚫 VPN Detected

⚠️ Disable VPN
And Try Again.</b>
""",
        parse_mode="HTML"
    )

    raise ReturnCommand()


# ================= CLONE APP DETECTED =================
elif (
    status == "fail"
    and "Clone App Detected" in message_txt
):

    bot.sendMessage(
        """
<b>🚫 Unofficial Telegram App Detected

⚠️ Please Use Official Telegram App
And Try Again.</b>
""",
        parse_mode="HTML"
    )

    raise ReturnCommand()


# ================= FAILED =================
else:

    User.saveData(
        "verify",
        "pending"
    )

    bot.sendMessage(
        """
<b>❌ Verification Failed

🔄 Please Try Again.</b>
""",
        parse_mode="HTML"
    )

    Bot.runCommand(
        "/PIRO_Verification"
    )

    raise ReturnCommand()
