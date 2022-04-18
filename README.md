# Bobs

*To look and observe what is actually happening on Bitcoin*

Bobs is a Bitcoin OBServatory meant to be easy to use and lightweight, it allows scanning and monitoring of Bitcoin
related data structures (blocks, mempool, more planned) given customizable filters.  
It requires no state, runs entirely in memory, and is well suited for pruned nodes.

* [Requirements](#Requirements)
* [Setup](#Setup)
    * [Easy way](#Easy-way)
    * [Recommended way](#Recommended-way)
* [Quickstart](#Quickstart)
* [Usage](#Usage)
    * [Settings](#Settings)
    * [Filters](#Filters)
        * [Keys](#Keys)
        * [Criteria](#Criteria)
    * [Target](#Target)
    * [Scan](#Scan)
    * [Details](#Details)

## Requirements

* Linux only, tested on Ubuntu and Debian. (Should be fairly easy to make it work on Windows or Mac)

* [Bitcoin Core](https://github.com/bitcoin/bitcoin) version equal or above [23.0](https://bitcoincore.org/bin/bitcoin-core-23.0/test.rc5/) (`bobs` requires [this](https://github.com/bitcoin/bitcoin/pull/22918) functionality).
The full node can be pruned, although this will limit the scan possibilities only to the stored blocks.

* Python 3.8+ (should be already installed with most Linux distros).

## Setup

Clone or download the repository.

Open a terminal from the Observatory folder and run `sudo apt install python3-pip` (it may not be necessary), then pick
one of the two below:

* ### Easy way

```bash
python3 -m pip install -e src/.
```

* ### Recommended way

```bash
sudo apt install python3-venv
python3 -m venv .env
source .env/bin/activate
pip3 install -e src/.
```

The recommended way is more complex, but it will keep your base system clean. If you decide to go for it, remember that
you'll have to run `source .env/bin/activate` as first command each time that you want to use the Observatory (check
for `(.env)` at the beginning of the lines in your terminal).

Lastly, activate the [REST](https://github.com/bitcoin/bitcoin/blob/master/doc/REST-interface.md) server from your full
node adding `rest = 1` to your `bitcoin.conf` file (or by passing `-rest` through CLI).

## Quickstart

## Usage

```bash
(.env) /home/user/observatory$ bobs -h
usage: bobs [-h] [-f FILTERS] [-d] [-t {blocks,mempool}] [-fmt FORMAT] [-se SETTINGS] {scan,monitor} ...

A Bitcoin observatory to monitor and scan given customizable filters

positional arguments:
  {scan,monitor}
    scan                Scan past data using given filters
    monitor             Monitor new coming data using given filter, currently not implemented

optional arguments:
  -h, --help            show this help message and exit
  -f FILTERS, --filters FILTERS
                        The name of the filters to use (they have to be declared in settings.toml)
  -d, --details         Increase result output details, can be set multiple times to amplify the effect
  -t {blocks,mempool}, --target {blocks,mempool}
                        What to scan, default is `blocks`
  -fmt FORMAT, --format FORMAT
                        Format to pass to tabulate() for table formatting. (default 'fancy_grid')
  -se SETTINGS, --settings SETTINGS
                        Path to settings.toml file, default is current directory. If file not present, create it
```

### Settings

The first thing to do is to create a `settings.toml` file, run any `bobs` command (e.g., `bobs scan`) and ignore the
error. It should have created the settings file in the same directory as you are in. To use a custom directory, pass
the `-se` option:

```bash
(.env) home/user/observatory$ bobs -se /home/user/ scan
```

### Filters

Give a look at the `settings.toml` file (more documentation for it is planned), and in particular at the filters. Those
are collection of criteria that represent the pattern you are looking for. The default settings include a few filters
that may be helpful as a reference.

This is the format of each filter:

```
[filters.{name}]
{key} = "{criterion}"
```

So a filter that represents a transaction with a certain TXID could look like:

```toml
[filters.txid]
txid = "Include('ff821fea070bed1220')"
```

* The `filters` part is a constant, it tells `bobs` that you are declaring a new filter.
* The `name` is completely arbitrary, the only restriction is that is has to be unique per `settings.toml` file.
* The `key` refers to which part of the candidate you want to pass as the actual candidate to the `criterion`, the complete list
  is below. If the key is invalid, `bobs` will pass the entire candidate.
* The `criterion` part accepts any of `bobs` criterion, the complete list is below. They all behave very similarly, they
  accept one or more values and represent a characterizing mark or trait that a candidate should have in order to match
  the `criterion`.

You can set as many filters as you want, with unlimited criterion each; when you are done, you can pass the desired filter names with the `-f` option:

#### Keys

* txid
* hash
* version
* size
* vsize
* weight
* locktime
* inputs
* outputs
* height
* timestamp_date
* date
* abs_fee
* rel_fee
* is_coinbase
* n_in
* n_out
* in_counter
* out_counter
* n_eq
* den
* inputs_sum
* outputs_sum
* addresses
* in_addrs
* out_addrs
* types
* in_types
* out_types
* input_values
* output_values

More are planned, the list is not at all stable, and more documentation is planned.

#### Criteria

* Greater
* Lesser
* Between
* Equal
* Different
* Include
* Appear
* Regex
* Satisfy

The list should be more or less stable, more documentation is planned.

### Target

With the `-t` or `--target` option you can specify which data structure to target. By default, it looks at the blocks 
in the most-work fully-validated chain (as provided by the full node), you can choose to look at the mempool instead by
passing `-t mempool`.

### Scan

```bash
(.env) /home/user/observatory$ bobs scan -h
usage: bobs scan [-h] [-s START] [-e END]

Scan past data using given filters

optional arguments:
  -h, --help            show this help message and exit
  -s START, --start START
                        Start block height
  -e END, --end END     End block height
```

Scan current available data in the chosen target, if you chose blocks you'll have to provide a `start` and `end`.

**Examples:**

`-s 100 -e 200`

Will search for transactions between block 100 and block 200 included.

You can give **negative** values to `start` and this will scan the last chosen blocks **depending** on the
`end` value.

`-s=-10 -e 0`

Will search for transactions in the last 10 blocks.

`-s=-10 -e 5`

Will search for transaction in 5 block starting from ten blocks ago.

### Details

You can pass the `-d` option to increase the amount of information displayed as a result. By default, only prints a list
of TXIDs that match the filters:

```bash
(.env) /home/user/observatory$ bobs -f coinbase scan -s=-10 -e 0

Choosen filters:
	coinbase filter

Full command used: /home/user/observatory/.env/bin/bobs -f coinbase scan -s=-10 -e 0

Requested scan from block 708798 to block 708807, included.

100%|█████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 10/10 [00:01<00:00,  5.56it/s]

Found 10 transaction:


ff821fea070bed1220804d1662bade5854b34cd60ee7513207a262413860f5ce
936224390735ec0a7f7d98a34f17367dc6a277d85de2b1a4d18a1f7091c11954
9eb92829a47c1fd7b2fd0333a1cbbcd9b4afa6067f99b45573dc33536bde2184
fa3fbf2b50d0423692c40c11d7a398eeef6854d9cd039eefc48a8bcc81f9fa44
dd42dd0940d15fdc11bec24b2b5c26ca84c2d116f38f08ecdc9ceee4f6cec637
d8748842fedc2950831f4019aea43f723eae4355dc3a226ed34dcfbd603d4ecf
aa33efa0a696f965cbd6999ab3ba4e3f352786e01e48274f378af92bb4662024
efa38a686985b402f0b1e1987b589d4cb107452c2f3c35d5f94ff5c2062fcf53
6580c33eb259cc6bbf46ba21d08a0342547a7cc30f3fc0e2aad661e2d522c321
e4063d95d6951870251890d71cb4ab3c415f66ae054a1a7103306fb9ef51e668
```

By adding the `-d` option you increase the details.

```bash
(.env) /home/user/observatory$ bobs -f coinbase -d scan -s=-10 -e 0

Choosen filters:
	coinbase filter

Full command used: /home/user/observatory/.env/bin/bobs -f coinbase -d scan -s=-10 -e 0

Requested scan from block 708798 to block 708807, included.

100%|█████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 10/10 [00:01<00:00,  5.45it/s]

Found 10 transaction:


╒══════════════════════════════════════════════════════════════════╤══════════╤══════════════════╕
│ txid                                                             │   height │ date             │
╞══════════════════════════════════════════════════════════════════╪══════════╪══════════════════╡
│ ff821fea070bed1220804d1662bade5854b34cd60ee7513207a262413860f5ce │   708798 │ 2021-11-08 14:38 │
├──────────────────────────────────────────────────────────────────┼──────────┼──────────────────┤
│ 9eb92829a47c1fd7b2fd0333a1cbbcd9b4afa6067f99b45573dc33536bde2184 │   708800 │ 2021-11-08 15:30 │
├──────────────────────────────────────────────────────────────────┼──────────┼──────────────────┤
│ 936224390735ec0a7f7d98a34f17367dc6a277d85de2b1a4d18a1f7091c11954 │   708799 │ 2021-11-08 14:57 │
├──────────────────────────────────────────────────────────────────┼──────────┼──────────────────┤
│ fa3fbf2b50d0423692c40c11d7a398eeef6854d9cd039eefc48a8bcc81f9fa44 │   708801 │ 2021-11-08 15:37 │
├──────────────────────────────────────────────────────────────────┼──────────┼──────────────────┤
│ d8748842fedc2950831f4019aea43f723eae4355dc3a226ed34dcfbd603d4ecf │   708803 │ 2021-11-08 15:40 │
├──────────────────────────────────────────────────────────────────┼──────────┼──────────────────┤
│ dd42dd0940d15fdc11bec24b2b5c26ca84c2d116f38f08ecdc9ceee4f6cec637 │   708802 │ 2021-11-08 15:39 │
├──────────────────────────────────────────────────────────────────┼──────────┼──────────────────┤
│ aa33efa0a696f965cbd6999ab3ba4e3f352786e01e48274f378af92bb4662024 │   708804 │ 2021-11-08 15:45 │
├──────────────────────────────────────────────────────────────────┼──────────┼──────────────────┤
│ efa38a686985b402f0b1e1987b589d4cb107452c2f3c35d5f94ff5c2062fcf53 │   708805 │ 2021-11-08 16:10 │
├──────────────────────────────────────────────────────────────────┼──────────┼──────────────────┤
│ 6580c33eb259cc6bbf46ba21d08a0342547a7cc30f3fc0e2aad661e2d522c321 │   708806 │ 2021-11-08 16:24 │
├──────────────────────────────────────────────────────────────────┼──────────┼──────────────────┤
│ e4063d95d6951870251890d71cb4ab3c415f66ae054a1a7103306fb9ef51e668 │   708807 │ 2021-11-08 16:25 │
```

You can pass the option multiple times (e.g, `-ddd` will print detailed information of each transaction, inputs and
outputs included).

---

Enjoy!
