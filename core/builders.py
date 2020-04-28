class BlocksBuilder():
    def __init__(self):
        self.reset()

    def reset(self):
        self._blocks = []

    @property
    def blocks(self):
        blocks = self._blocks
        self.reset()
        return blocks

    @property
    def has_block(self):
        return len(self._blocks) > 0

    def add_block(self, block):
        self._blocks.append(block)

    def add_blocks(self, blocks):
        self._blocks.extend(blocks)

    def add_divider(self):
        self._blocks.append({"type": "divider"})


class SectionBuilder():
    def __init__(self):
        self.reset()

    def reset(self):
        self._text = []
        self._accessory = []

    @property
    def section(self):
        text = "".join(self._text)
        block = {"type": "section"}

        if (self._text):
            block['text'] = {
                "type": "mrkdwn",
                "text": text
            }

        if (self._accessory):
            block['accessory'] = self._accessory

        self.reset()
        return block

    def add_text(self, text):
        self._text.append(text)

    def add_button(self, text, value, button_type='plain_text', emoji=True):
        self._accessory = {
            "type": "button",
            "text": {
                "type": button_type,
                "text": text,
                "emoji": emoji
            },
            "value": value
        }

    def format_text(self, **kwargs):
        self._text = "".join(self._text).format(**kwargs)


class ActionsBuilder():
    def __init__(self):
        self.reset()

    def reset(self):
        self._elements = []

    @property
    def actions(self):
        elements = "".join(self._elements)
        self.reset()
        return {
            "type": "actions",
            "elements": elements
        }

    def add_button(self, text, value):
        self._elements.append({
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": text
            },
            "value": value
        })
