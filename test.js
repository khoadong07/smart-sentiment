const io = require('socket.io-client');

const socket = io('http://0.0.0.0:5001');

socket.on('connect', () => {
    console.log('Connected to server');
    socket.emit('predict', {
        data: [{
            id: '7521631307152084231_3',
            topic_name: 'Vinamilk',
            type: 'NEWS_TOPIC',
            topic_id: '5cd2a99d2e81050a12e5339a',
            siteId: '7427331267015197703',
            siteName: 'baothegioisua',
            title: 'Vinamilk dính nghi vấn lừa đảo cộng tác viên qua app nhập liệu',
            content: 'Nhiều người phản ánh bị treo tiền, không hoàn tiền khi làm cộng tác viên qua nền tảng app được cho là của Vinamilk. Một số nghi ngờ đây là hình thức lừa đảo tinh vi.',
            description: '',
            is_kol: false,
            total_interactions: 57
        }]
    });
});

socket.on('result', (data) => {
    console.log('Received result:', data);
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
});