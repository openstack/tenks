Veth Pair
=========

This role manages a veth pair. Actions:

  * If `veth_pair_state` is `present`, it will create the veth pair and
    plug one end into the specified OVS bridge. If `veth_pair_plug_into_source`
    is enabled, it will also plug the other end into/from a source Linux
    bridge.

  * If `veth_pair_state` is `absent`, it will ensure the veth pair does not exist; if
    `veth_pair_plug_into_source` is also enabled, it will ensure the veth pair is
    not plugged into the source bridge.

Requirements
------------

The host should have the `ip` and `ovs-vsctl` commands accessible.

Role Variables
--------------

- `veth_pair_ovs_link_name`: The name to give the veth link that plugs into the
  OVS bridge.
- `veth_pair_ovs_bridge`: The name of the OVS bridge to plug into.
- `veth_pair_source_link_name`: The name to give the veth link that plugs into
  the source device.
- `veth_pair_source_bridge`: The name of the source Linux bridge to plug into. Must be
  specified if and only if `veth_pair_plug_into_source` is enabled.
- `veth_pair_plug_into_source`: Whether or not to plug the source end of the
  veth pair into a Linux bridge. If enabled, `veth_pair_source_bridge` must
  also be specified. Default is `false`.
- `veth_pair_state`: Whether or not the veth pair should exist. Choose from
  `present` or `absent`. Default is `present`.
