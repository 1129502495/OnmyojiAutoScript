# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
import time

import numpy as np

from enum import Enum
from cached_property import cached_property

from module.base.timer import Timer
from tasks.base_task import BaseTask
from tasks.Component.GeneralInvite.assets import GeneralInviteAssets
from tasks.Component.GeneralInvite.config_invite import InviteConfig, InviteNumber, FindMode
from module.logger import logger


class FriendList(str, Enum):
    RECENT_FRIEND = 'recent_friend'
    GUILD_FRIEND = 'guild_friend'
    FRIEND = 'friend'
    OTHER_FRIEND = 'other_friend'


class RoomType(str, Enum):
    # 房间只可以两个人的： 探索
    NORMAL_2 = 'normal_2'
    # 房间可以两三个人的： 觉醒、御魂、日轮、石距（石距是单次没有锁定阵容）
    NORMAL_3 = 'normal_3'
    # 永生之海不一样
    ETERNITY_SEA = 'eternity_sea'
    # 经验妖怪和金币妖怪
    NORMAL_5 = 'normal_5'


class GeneralInvite(BaseTask, GeneralInviteAssets):
    timer_invite = None
    timer_wait = None

    def run_invite(self, config: InviteConfig, is_first: bool = False) -> bool:
        """
        队长！！身份。。。在组件界面邀请好友（ 如果开启is_first） 等待队员进入开启挑战
        :param config:
        :param is_first: 如果是第一次开房间的那就要邀请队员，其他情况等待队员进入
        :return:
        """
        logger.hr('Invite friend', 2)
        if not self.ensure_enter():
            logger.warning('Not enter invite page')
            return False
        if is_first:
            _ = self.room_type
            self.timer_invite = Timer(20)
            self.timer_invite.start()
            self.ensure_room_type(config.invite_number)
            self.invite_friends(config)
        wait_second = config.wait_time.second + config.wait_time.minute * 60
        self.timer_wait = Timer(wait_second)
        self.timer_wait.start()
        while 1:
            self.screenshot()
            if self.timer_wait.reached():
                logger.warning('Wait timeout')
                return False
            if self.timer_invite and self.timer_invite.reached():
                logger.info('Invitation is triggered every 20s')
                self.timer_invite.reset()
                self.invite_friends(config)

            if self.appear(self.I_MATCHING):
                logger.warning('Timeout, now is no room')
                return False


            # 如果这个房间最多只容纳两个人（意思是只可以邀请一个人），且已经邀请一个人了，那就开启挑战
            if self.room_type == RoomType.NORMAL_2 and not self.appear(self.I_ADD_2):
                logger.info('Start challenge and this room can only invite one friend')
                while 1:
                    self.screenshot()
                    if not self.appear(self.I_FIRE):
                        break
                    if self.appear_then_click(self.I_FIRE, interval=1):
                        continue
                return True
            # 如果这个房间最多容纳三个人（意思是可以邀请两个人），且设定邀请一个就开启挑战，那就开启挑战
            elif self.room_type == RoomType.NORMAL_3 and config.invite_number == InviteNumber.ONE and not self.appear(self.I_ADD_1):
                logger.info('Start challenge and user only invite one friend')
                while 1:
                    self.screenshot()
                    if not self.appear(self.I_FIRE):
                        break
                    if self.appear_then_click(self.I_FIRE, interval=1):
                        continue
                return True
            # 如果这个房间最多容纳三个人（意思是可以邀请两个人），且设定邀请两个就开启挑战，那就开启挑战
            elif self.room_type == RoomType.NORMAL_3 \
                    and config.invite_number == InviteNumber.TWO and not self.appear(self.I_ADD_2):
                logger.info('Start challenge and user invite two friends')
                while 1:
                    self.screenshot()
                    if not self.appear(self.I_FIRE):
                        break
                    if self.appear_then_click(self.I_FIRE, interval=1):
                        continue
                return True
            # 如果这个房间是五人的，且设定邀请一个就开启挑战，那就开启挑战
            elif self.room_type == RoomType.NORMAL_5 \
                    and config.invite_number == InviteNumber.ONE and not self.appear(self.I_ADD_5_1):
                logger.info('Start challenge and user only invite one friend')
                while 1:
                    self.screenshot()
                    if not self.appear(self.I_FIRE):
                        break
                    if self.appear_then_click(self.I_FIRE, interval=1):
                        continue
                return True
            # 如果这个房间是五人的，且设定邀请两个就开启挑战，那就开启挑战
            elif self.room_type == RoomType.NORMAL_5 \
                    and config.invite_number == InviteNumber.TWO and not self.appear(self.I_ADD_5_2):
                logger.info('Start challenge and user invite two friends')
                while 1:
                    self.screenshot()
                    if not self.appear(self.I_FIRE):
                        break
                    if self.appear_then_click(self.I_FIRE, interval=1):
                        continue
                return True
            # 如果是永生之海
            elif self.room_type == RoomType.ETERNITY_SEA and not self.appear(self.I_ADD_SEA):
                logger.info('Start challenge and this is lock sea')
                while 1:
                    self.screenshot()
                    if not self.appear(self.I_FIRE_SEA):
                        break
                    if self.appear_then_click(self.I_FIRE_SEA, interval=1):
                        continue
                return True

    def ensure_enter(self) -> bool:
        """
        确认是否进入了组队界面
        :return:
        """
        logger.info('Ensure enter invite page')
        while 1:
            self.screenshot()
            if self.appear(self.I_ADD_2):
                return True
            if self.appear(self.I_ADD_5_4):
                return True
            if self.appear(self.I_LOCK_SEA):
                return True
            if self.appear(self.I_UNLOCK_SEA):
                return True
            if self.appear(self.I_MATCHING):
                return False

    @cached_property
    def room_type(self) -> RoomType:
        """
        只需要在队长进入的时候判断一次就可以了，任务后面之间使用

        :return:
        """
        self.screenshot()
        room_type = self.check_room_type(image=self.device.image)
        logger.info(f'Room type: {room_type}')
        return room_type

    def check_room_type(self, image: np.array = None, pre_type: RoomType = None) -> RoomType:
        """
        检查房间类型
        :param image:
        :param pre_type: 可以先指定这个类型，如果不指定，就自动检查
        :return:
        """

        def check_3(img) -> bool:
            appear = False
            if self.I_ADD_1.match(img) and self.I_ADD_2.match(img):
                appear = True
            return appear

        def check_2(img) -> bool:
            appear = False
            if not self.I_ADD_1.match(img) and self.I_ADD_2.match(img):
                appear = True
            return appear

        def check_5(img) -> bool:
            appear = False
            if self.I_ADD_5_1.match(img) and self.I_ADD_5_2.match(img) \
                    and self.I_ADD_5_3.match(img) and self.I_ADD_5_4.match(img):
                appear = True
            return appear

        def check_eternity_sea(img) -> bool:
            appear = False
            if self.I_LOCK_SEA.match(img) or self.I_UNLOCK_SEA.match(img):
                appear = True
            return appear

        room_type = None
        if pre_type is not None:
            match pre_type:
                case RoomType.NORMAL_2:
                    room_type = RoomType.NORMAL_2 if check_2(image) else None
                case RoomType.NORMAL_3:
                    room_type = RoomType.NORMAL_3 if check_3(image) else None
                case RoomType.NORMAL_5:
                    room_type = RoomType.NORMAL_5 if check_5(image) else None
                case RoomType.ETERNITY_SEA:
                    room_type = RoomType.ETERNITY_SEA if check_eternity_sea(image) else None
        if room_type:
            return room_type
        if room_type is None and check_2(image):
            room_type = RoomType.NORMAL_2
            return room_type
        if room_type is None and check_3(image):
            room_type = RoomType.NORMAL_3
            return room_type
        if room_type is None and check_5(image):
            room_type = RoomType.NORMAL_5
            return room_type
        if room_type is None and check_eternity_sea(image):
            room_type = RoomType.ETERNITY_SEA
            return room_type
        return room_type

    def ensure_room_type(self, friend_number: int = None) -> bool:
        """
        确认设定的邀请人数是否会超出房间的最大
        :param friend_number: 这个输入的是用户选项中的invite_number
        :return:  如果超出了，就返回False
        """
        if isinstance(friend_number, InviteNumber):
            if friend_number == InviteNumber.ONE:
                friend_number = 1
            elif friend_number == InviteNumber.TWO:
                friend_number = 2

        if friend_number == 2:
            if self.room_type == RoomType.NORMAL_2:
                # 整个房间就可以两个人，还邀请两个 这个是报错的
                logger.error('Room can only be one people, but invite two people')
                return False
            elif self.room_type == RoomType.ETERNITY_SEA:
                # 永生之海，只能邀请一个人
                logger.error('Room can only be one people, but invite two people')
                return False
            return True
        return True

    @cached_property
    def friend_class(self) -> list[str]:
        return ['好友', '最近', '跨区', '寮友', '蔡友', '路区', '察友', '区']

    def detect_select(self, name: str = None) -> bool:
        """
        在当前的页面检测是否有好友， 如果有就选中这个好友
        :return:
        """
        if not name:
            return False

        self.screenshot()
        self.O_FRIEND_NAME_1.keyword = name
        self.O_FRIEND_NAME_2.keyword = name
        appear_1 = self.ocr_appear_click(self.O_FRIEND_NAME_1, interval=2)
        appear_2 = self.ocr_appear_click(self.O_FRIEND_NAME_2, interval=2)
        if not appear_1 and not appear_2:
            logger.info('Current page no friend')
            return False

        while appear_1 or appear_2:
            self.screenshot()
            if self.appear(self.I_SELECTED):
                break
            appear_1 = self.ocr_appear_click(self.O_FRIEND_NAME_1, interval=2)
            appear_2 = self.ocr_appear_click(self.O_FRIEND_NAME_2, interval=2)

        return True

    def invite_friend(self, name: str = None, find_mode: FindMode = None) -> bool:
        """
        邀请好友
        :param find_mode: 寻找的方式
        :param name:
        :return:
        """
        logger.info('Click add to invite friend')
        # 点击＋号
        while 1:
            self.screenshot()
            if self.appear(self.I_LOAD_FRIEND):
                break
            if self.appear(self.I_INVITE_ENSURE):
                break
            if self.appear_then_click(self.I_ADD_2, interval=1):
                continue
            if self.appear_then_click(self.I_ADD_5_4, interval=1):
                continue

        friend_class = []
        class_ocr = [self.O_F_LIST_1, self.O_F_LIST_2, self.O_F_LIST_3, self.O_F_LIST_4]
        class_index = 0
        list_1 = self.O_F_LIST_1.ocr(self.device.image)
        list_2 = self.O_F_LIST_2.ocr(self.device.image)
        list_3 = self.O_F_LIST_3.ocr(self.device.image)
        list_4 = self.O_F_LIST_4.ocr(self.device.image)
        if list_1 is not None and list_1 != '' and list_1 in self.friend_class:
            friend_class.append(list_1)
        if list_2 is not None and list_2 != '' and list_2 in self.friend_class:
            friend_class.append(list_2)
        if list_3 is not None and list_3 != '' and list_3 in self.friend_class:
            friend_class.append(list_3)
        if list_4 is not None and list_4 != '' and list_4 in self.friend_class:
            friend_class.append(list_4)
        for i in range(len(friend_class)):
            if friend_class[i] == '蔡友':
                friend_class[i] = '寮友'
            elif friend_class[i] == '路区':
                friend_class[i] = '跨区'
            elif friend_class[i] == '察友':
                friend_class[i] = '寮友'
            elif friend_class[i] == '区':
                friend_class[i] = '跨区'
        logger.info(f'Friend class: {friend_class}')

        is_select: bool = False  # 是否选中了好友
        if find_mode == FindMode.RECENT_FRIEND:
            logger.info('Find recent friend')
            # 获取’最近‘在friend_class中的index
            if '最近' not in friend_class:
                logger.warning('No recent friend')
                return False
            recent_index = friend_class.index('最近')
            while recent_index == 1:
                self.screenshot()
                if self.appear(self.I_FLAG_2_ON):
                    break
                if self.appear_then_click(self.I_FLAG_2_OFF, interval=1):
                    continue

            logger.info(f'Now find friend in ”最近“')
            time.sleep(1)
            if not is_select:
                if self.detect_select(name):
                    is_select = True
            time.sleep(1)
            if not is_select:
                if self.detect_select(name):
                    is_select = True

        for index in range(len(friend_class)):
            # 如果不是自动寻找，就跳过
            if find_mode != FindMode.AUTO_FIND:
                continue
            # 如果已经选中了好友，就不需要再选中了
            if is_select:
                continue
            # 首先切换到不同的好友列表
            while index == 0:
                self.screenshot()
                if self.appear(self.I_FLAG_1_ON):
                    break
                if self.appear_then_click(self.I_FLAG_1_OFF, interval=1):
                    continue
            while index == 1:
                self.screenshot()
                if self.appear(self.I_FLAG_2_ON):
                    break
                if self.appear_then_click(self.I_FLAG_2_OFF, interval=1):
                    continue
            while index == 2:
                self.screenshot()
                if self.appear(self.I_FLAG_3_ON):
                    break
                if self.appear_then_click(self.I_FLAG_3_OFF, interval=1):
                    continue
            while index == 3:
                self.screenshot()
                if self.appear(self.I_FLAG_4_ON):
                    break
                if self.appear_then_click(self.I_FLAG_4_OFF, interval=1):
                    continue

            # 选中好友， 在这里游戏获取在线的好友并不是很快，根据不同的设备会有不同的时间，而且没有什么元素提供我们来判断
            # 所以这里就直接等待一段时间
            logger.info(f'Now find friend in {friend_class[index]}')
            time.sleep(1)
            if not is_select:
                if self.detect_select(name):
                    is_select = True
            time.sleep(1)
            if not is_select:
                if self.detect_select(name):
                    is_select = True

        # 点击确定
        logger.info('Click invite ensure')
        if not self.appear(self.I_INVITE_ENSURE):
            logger.warning('No appear invite ensure while invite friend')
        while 1:
            self.screenshot()
            if not self.appear(self.I_INVITE_ENSURE):
                break
            if self.appear_then_click(self.I_INVITE_ENSURE):
                continue
        # 哪怕没有找到好友也有点击 确认 以退出好友列表
        if not is_select:
            logger.warning('No find friend')
            # 这个时候任务运行失败
            logger.info('Task failed')
            return False

        return True

    def invite_friends(self, config: InviteConfig) -> bool:
        """
        看情况邀请两个好友
        :return:
        """
        success = self.invite_friend(config.friend_1, config.find_mode)
        if not success:
            logger.warning('Invite friend 1 failed')
        # 如果是邀请第二个人
        if config.invite_number == InviteNumber.TWO:
            success = self.invite_friend(config.friend_2, config.find_mode)
            if not success:
                logger.warning('Invite friend 2 failed')
        time.sleep(0.5)

if __name__ == '__main__':
    from module.config.config import Config
    from module.device.device import Device
    import cv2

    c = Config('oas1')
    d = Device(c)
    t = GeneralInvite(c, d)
    # t.invite_friend('城凉文月', FindMode.RECENT_FRIEND)
    t.run_invite(c.orochi.invite_config, is_first=True)