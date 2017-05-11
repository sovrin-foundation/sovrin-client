from copy import copy, deepcopy

import pytest

from sovrin_node.test import waits
from stp_core.loop.eventually import eventually
from plenum.common.constants import VERSION
from sovrin_common.constants import ACTION, CANCEL, JUSTIFICATION
from sovrin_node.test.upgrade.helper import checkUpgradeScheduled, \
    checkNoUpgradeScheduled
from sovrin_node.test.upgrade.conftest import validUpgrade


@pytest.fixture(scope='module')
def nodeIds(poolNodesStarted):
    return next(iter(poolNodesStarted.nodes.values())).poolManager.nodeIds


@pytest.fixture(scope="module")
def poolUpgradeSubmitted(be, do, trusteeCli, validUpgrade, trusteeMap):
    do('send POOL_UPGRADE name={name} version={version} sha256={sha256} '
       'action={action} schedule={schedule} timeout={timeout}',
       within=10,
       expect=['Pool upgrade successful'], mapper=validUpgrade)


@pytest.fixture(scope="module")
def poolUpgradeScheduled(poolUpgradeSubmitted, poolNodesStarted, validUpgrade):
    nodes = poolNodesStarted.nodes.values()
    timeout = waits.expectedUpgradeScheduled()
    poolNodesStarted.looper.run(
        eventually(checkUpgradeScheduled, nodes,
                   validUpgrade[VERSION], retryWait=1, timeout=timeout))


@pytest.fixture(scope="module")
def poolUpgradeCancelled(poolUpgradeScheduled, be, do, trusteeCli,
                         validUpgrade, trusteeMap):
    validUpgrade = copy(validUpgrade)
    validUpgrade[ACTION] = CANCEL
    validUpgrade[JUSTIFICATION] = '"not gonna give you one"'

    do('send POOL_UPGRADE name={name} version={version} sha256={sha256} '
       'action={action} justification={justification}',
       within=10,
       expect=['Pool upgrade successful'], mapper=validUpgrade)


def testOnlyTrusteeCanSendPoolUpgrade(looper, steward, validUpgrade):
    # A steward sending POOL_UPGRADE but txn fails
    stClient, stWallet = steward
    validUpgrade = deepcopy(validUpgrade)
    validUpgrade[NAME] = 'upgrade-20'
    validUpgrade[VERSION] = bumpedVersion()
    _, req = sendUpgrade(stClient, stWallet, validUpgrade)
    timeout = plenumWaits.expectedReqNAckQuorumTime()
    looper.run(eventually(checkNacks, stClient, req.reqId,
                          'cannot do', retryWait=1, timeout=timeout))


def testPoolUpgradeSent(poolUpgradeScheduled):
    pass


def testPoolUpgradeCancelled(poolUpgradeCancelled, poolNodesStarted):
    nodes = poolNodesStarted.nodes.values()
    timeout = waits.expectedNoUpgradeScheduled()
    poolNodesStarted.looper.run(
        eventually(checkNoUpgradeScheduled,
                   nodes, retryWait=1, timeout=timeout))
