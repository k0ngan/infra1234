[bits 16]
[org 0x7C00]

SERIAL_PORT equ 0x3F8

start:
    cli
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7C00
    sti

    call init_serial

    mov si, message
    call print_vga

    mov si, message
    call print_serial

    mov dx, 0x0F4
    xor al, al
    out dx, al

halt:
    hlt
    jmp halt

print_vga:
    lodsb
    test al, al
    jz .done
    mov ah, 0x0E
    mov bh, 0x00
    mov bl, 0x07
    int 0x10
    jmp print_vga
.done:
    ret

init_serial:
    mov dx, SERIAL_PORT + 1
    xor al, al
    out dx, al

    mov dx, SERIAL_PORT + 3
    mov al, 0x80
    out dx, al

    mov dx, SERIAL_PORT + 0
    mov al, 0x03
    out dx, al

    mov dx, SERIAL_PORT + 1
    xor al, al
    out dx, al

    mov dx, SERIAL_PORT + 3
    mov al, 0x03
    out dx, al

    mov dx, SERIAL_PORT + 2
    mov al, 0xC7
    out dx, al

    mov dx, SERIAL_PORT + 4
    mov al, 0x0B
    out dx, al
    ret

print_serial:
    lodsb
    test al, al
    jz .done
    push ax
    call serial_write_byte
    pop ax
    jmp print_serial
.done:
    ret

serial_write_byte:
    mov ah, al
.wait:
    mov dx, SERIAL_PORT + 5
    in al, dx
    test al, 0x20
    jz .wait
    mov dx, SERIAL_PORT
    mov al, ah
    out dx, al
    ret

message db 'Boot OK: Micro S.O. UTEM', 13, 10, 0

times 510 - ($ - $$) db 0
dw 0xAA55
