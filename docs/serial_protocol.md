# Serial Protocol

Default V2 message:

```text
@T,seq,found,dx,dy,confidence\n
```

Lost target:

```text
@T,seq,0,0,0,0\n
```

Legacy mode:

```text
@T,found,dx,dy,confidence\n
```

The sender always emits lost frames instead of going silent. This lets TI Bridge distinguish target loss from communication timeout.
