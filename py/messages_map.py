#!/usr/bin/env python
from collections import defaultdict
from messages_pb2 import MessageType
from types_pb2 import wire_in, wire_out, wire_debug_in, wire_debug_out, wire_tiny, wire_bootloader

# len("MessageType_MessageType_") - len("_fields") == 17
TEMPLATE = "\t{{ {type} {dir} {msg_id:46} {fields:29} {process_func} }},"

LABELS = {
    wire_in: "in messages",
    wire_out: "out messages",
    wire_debug_in: "debug in messages",
    wire_debug_out: "debug out messages",
}

def handle_message(message, extension):
    name = message.name
    short_name = name.split("MessageType_", 1).pop()
    assert(short_name != name)

    interface = "d" if extension in (wire_debug_in, wire_debug_out) else "n"
    direction = "i" if extension in (wire_in, wire_debug_in) else "o"

    options = message.GetOptions()
    bootloader = options.Extensions[wire_bootloader]
    tiny = options.Extensions[wire_tiny] and direction == "i"

    if getattr(options, 'deprecated', None):
        return '\t// Message %s is deprecated' % short_name
    if bootloader:
        return '\t// Message %s is used in bootloader mode only' % short_name
    if tiny:
        return '\t// Message %s is used in tiny mode' % short_name

    return TEMPLATE.format(
        type="'%c'," % interface,
        dir="'%c'," % direction,
        msg_id="MessageType_%s," % name,
        fields="%s_fields," % short_name,
        process_func = "(void (*)(void *)) fsm_msg%s" % short_name if direction == "i" else "0"
    )

print('\t// This file is automatically generated by messages_map.py -- DO NOT EDIT!')

messages = defaultdict(list)

for message in MessageType.DESCRIPTOR.values:
    extensions = message.GetOptions().Extensions

    for extension in (wire_in, wire_out, wire_debug_in, wire_debug_out):
        if extensions[extension]:
            messages[extension].append(message)

for extension in (wire_in, wire_out, wire_debug_in, wire_debug_out):
    if extension == wire_debug_in:
        print("\n#if DEBUG_LINK")

    print("\n\t// {label}\n".format(label=LABELS[extension]))

    for message in messages[extension]:
        print(handle_message(message, extension))

    if extension == wire_debug_out:
        print("\n#endif")
