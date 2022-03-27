import brownie
from brownie import Auction, Weth, Nft
import pytest
from scripts.useful import get_account
import time

ACCOUNT = get_account(1)
BIDDER = get_account(2)
TOKEN_ID = 18


@pytest.fixture
def create_auction(deploy_auction, nft):
    auction = deploy_auction[0]
    weth = deploy_auction[1]
    starting_price = 10 ** 18
    starting_timestamp = int(time.time()) + 10
    ending_timestamp = starting_timestamp + 30

    nft.approve(auction, TOKEN_ID, {"from": ACCOUNT})

    auction.createAuction(nft, TOKEN_ID, starting_price,
                          starting_timestamp, ending_timestamp, {"from": ACCOUNT})

    time.sleep(10)

    return auction, nft, weth


@pytest.fixture
def deploy_auction():
    weth = Weth.deploy({"from": BIDDER})
    return Auction.deploy(weth, {"from": ACCOUNT}), weth


@pytest.fixture
def nft():
    return Nft.deploy({"from": ACCOUNT})


def test_cant_create_auction_not_owner(deploy_auction, nft):
    starting_price = 10 ** 18
    starting_timestamp = int(time.time()) + 10
    ending_timestamp = starting_timestamp + 35

    with brownie.reverts("The sender doesn't own NFT!"):
        deploy_auction[0].createAuction(nft, TOKEN_ID, starting_price,
                                        starting_timestamp, ending_timestamp, {"from": BIDDER})


def test_cant_create_auction_started(create_auction):
    auction = create_auction[0]
    nft = create_auction[1]
    starting_price = 10 ** 18
    starting_timestamp = int(time.time()) + 10
    ending_timestamp = starting_timestamp + 35

    with brownie.reverts("The auction already started by the owner!"):
        auction.createAuction(nft, TOKEN_ID, starting_price,
                              starting_timestamp, ending_timestamp, {"from": ACCOUNT})


def test_cant_create_auction_timestamp_false(deploy_auction, nft):
    starting_price = 10 ** 18
    starting_timestamp = int(time.time()) - 60
    ending_timestamp = starting_timestamp + 35

    with brownie.reverts("startingTimestamp must be greater than now!"):
        deploy_auction[0].createAuction(nft, TOKEN_ID, starting_price,
                                        starting_timestamp, ending_timestamp, {"from": ACCOUNT})


def test_cant_create_auction_nft_not_approved(deploy_auction, nft):
    starting_price = 10 ** 18
    starting_timestamp = int(time.time()) + 60
    ending_timestamp = starting_timestamp + 35

    with brownie.reverts("The NFT is not approved!"):
        deploy_auction[0].createAuction(nft, TOKEN_ID, starting_price,
                                        starting_timestamp, ending_timestamp, {"from": ACCOUNT})


def test_create_auction(create_auction):
    auction = create_auction[0]
    nft = create_auction[1]

    assert auction.allAuctions(nft, TOKEN_ID)[-1] == ACCOUNT  # seller

    assert auction.allAuctions(nft, TOKEN_ID)[2] == 10 ** 18  # starting price


def test_cant_bid_ended(create_auction):
    auction = create_auction[0]
    nft = create_auction[1]
    weth = create_auction[2]

    weth.approve(auction, 10 ** 19, {"from": BIDDER})

    time.sleep(35)

    with brownie.reverts("The auction is over!"):
        auction.bid(nft, TOKEN_ID, 10 ** 19, {"from": BIDDER})


def test_cant_bid_lower_amount(create_auction):
    auction = create_auction[0]
    nft = create_auction[1]
    weth = create_auction[2]

    weth.approve(auction, 10 ** 18, {"from": BIDDER})

    with brownie.reverts("The amount must be greater than the starting price!"):
        auction.bid(nft, TOKEN_ID, 10 ** 17, {"from": BIDDER})


def test_cant_bid_seller(create_auction):
    auction = create_auction[0]
    nft = create_auction[1]

    with brownie.reverts("The seller can not bid!"):
        auction.bid(nft, TOKEN_ID, 10 ** 19, {"from": ACCOUNT})


def test_cant_bid_weth_not_approve(create_auction):
    auction = create_auction[0]
    nft = create_auction[1]

    with brownie.reverts("The amount is not approved!"):
        auction.bid(nft, TOKEN_ID, 10 ** 19, {"from": BIDDER})


def test_bid(create_auction):
    auction = create_auction[0]
    nft = create_auction[1]
    weth = create_auction[2]

    weth.approve(auction, 10 ** 19, {"from": BIDDER})

    auction.bid(nft, TOKEN_ID, 10 ** 19, {"from": BIDDER})

    assert auction.allAuctions(nft, TOKEN_ID)[3] == 10 ** 19  # highest bid

    assert auction.allAuctions(nft, TOKEN_ID)[4] == BIDDER  # highest bidder


def test_cant_update_timestamp_ended(create_auction):
    auction = create_auction[0]
    nft = create_auction[1]
    new_timestamp = int(time.time()) + 10

    time.sleep(35)

    with brownie.reverts("The auction is over!"):
        auction.updateEndingTimestamp(
            nft, TOKEN_ID, new_timestamp, {"from": ACCOUNT})


def test_cant_update_timestamp_not_woner(create_auction):
    auction = create_auction[0]
    nft = create_auction[1]
    new_timestamp = int(time.time()) + 10

    with brownie.reverts("The sender is not the seller!"):
        auction.updateEndingTimestamp(
            nft, TOKEN_ID, new_timestamp, {"from": BIDDER})


def test_update_timestamp(create_auction):
    auction = create_auction[0]
    nft = create_auction[1]
    new_timestamp = int(time.time()) + 10

    auction.updateEndingTimestamp(
        nft, TOKEN_ID, new_timestamp, {"from": ACCOUNT})

    assert auction.allAuctions(nft, TOKEN_ID)[1] == new_timestamp


def test_cant_update_price_ended(create_auction):
    auction = create_auction[0]
    nft = create_auction[1]
    new_price = 10 ** 17

    time.sleep(35)

    with brownie.reverts("The auction is over!"):
        auction.updateStartingPrice(
            nft, TOKEN_ID, new_price, {"from": ACCOUNT})


def test_cant_update_price_not_woner(create_auction):
    auction = create_auction[0]
    nft = create_auction[1]
    new_price = 10 ** 17

    with brownie.reverts("The sender is not the seller!"):
        auction.updateStartingPrice(nft, TOKEN_ID, new_price, {"from": BIDDER})


def test_update_price(create_auction):
    auction = create_auction[0]
    nft = create_auction[1]
    new_price = 10 ** 17

    auction.updateStartingPrice(nft, TOKEN_ID, new_price, {"from": ACCOUNT})

    assert auction.allAuctions(nft, TOKEN_ID)[2] == new_price


def test_cant_end_not_ended(create_auction):
    auction = create_auction[0]
    nft = create_auction[1]

    with brownie.reverts("The auction is not over!"):
        auction.endAuction(nft, TOKEN_ID, {"from": ACCOUNT})


def test_end(create_auction):
    auction = create_auction[0]
    nft = create_auction[1]

    time.sleep(35)

    auction.endAuction(nft, TOKEN_ID, {"from": ACCOUNT})

    assert auction.allAuctions(
        nft, TOKEN_ID)[-1] == "0x0000000000000000000000000000000000000000"


def test_cant_force_reset_ended(create_auction):
    auction = create_auction[0]
    nft = create_auction[1]

    time.sleep(35)

    auction.endAuction(nft, TOKEN_ID, {"from": ACCOUNT})

    with brownie.reverts("The auction has already ended!"):
        auction.forceReset(nft, TOKEN_ID, {"from": ACCOUNT})


def test_cant_force_reset_ongoing(create_auction):
    auction = create_auction[0]
    nft = create_auction[1]

    with brownie.reverts("You can only force reset after 7 days!"):
        auction.forceReset(nft, TOKEN_ID, {"from": ACCOUNT})


def test_cant_force_reset_ended_before_7_days(create_auction):
    auction = create_auction[0]
    nft = create_auction[1]

    time.sleep(35)

    with brownie.reverts("You can only force reset after 7 days!"):
        auction.forceReset(nft, TOKEN_ID, {"from": ACCOUNT})


def test_force_reset(create_auction):
    auction = create_auction[0]
    nft = create_auction[1]

    time.sleep((7*24*60*60)+30)  # 7 days

    auction.forceReset(nft, TOKEN_ID, {"from": ACCOUNT})

    assert auction.allAuctions(
        nft, TOKEN_ID)[-1] == "0x0000000000000000000000000000000000000000"
