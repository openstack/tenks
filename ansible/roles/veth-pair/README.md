Veth Pair
=========

This role creates a veth pair. It will plug one end into the specified OVS
bridge and, optionally, can plug the other end into a source Linux bridge.

Requirements
------------

The host should have the `ip` and `ovs-vsctl` commands accessible. If
`veth_pair_plug_into_source` is enabled, the command `brctl` must also be
accessible.

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
