from anjani import command, plugin, util
from typing import Optional
from aiopath import AsyncPath

from pyrogram.types import (
    Message,
)

class OcrPlugin(plugin.Plugin):
    name = "OCR Plugin"

    async def run_ocr(self, message: Message) -> Optional[str]:
        """Run tesseract"""
        try:
            image = AsyncPath(await message.download())
        except Exception as e:  # skipcq: PYL-W0703
            return self.log.warning(
        "Failed to download image from MessageID %s in Chat %s",
        message.id,
        message.chat.id,
        )

        try:
            stdout, _, exitCode = await util.system.run_command(
                "tesseract", str(image), "stdout", "-l", "eng+ind", "--psm", "6"
            )
        except FileNotFoundError:
            return
        except Exception as e:  # skipcq: PYL-W0703
            return self.log.error("Unexpected error occured when running OCR", exc_info=e)
        finally:
            await image.unlink()

        if exitCode != 0:
            return self.log.warning("tesseract returned code '%s', %s", exitCode, stdout)

        return stdout

    async def cmd_ocr(self, ctx: command.Context) -> None:
        user_id = None
        reply_msg = ctx.msg.reply_to_message

        if reply_msg:
            content = reply_msg.text or reply_msg.caption
            if reply_msg.from_user and reply_msg.from_user.id != ctx.author.id:
                user_id = reply_msg.from_user.id
            elif reply_msg.forward_from:
                user_id = reply_msg.forward_from.id
        else:
            content = ctx.input

        if reply_msg and reply_msg.photo:
            ocr_result = await self.run_ocr(reply_msg)
            if ocr_result:
                try:
                    await self.bot.client.send_message(ctx.chat.id, ocr_result)
                except Exception as e:  # skipcq: PYL-W0703
                    await self.log.error("Failed to marked OCR results as spam", exc_info=e)

                # Return early if content is empty, so error message not shown
                if not content:
                    return None

        if not content:
            return await ctx.get_text("")
