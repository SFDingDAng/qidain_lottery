let ticketCardId = []
const fileObj = {};
    // 获取HTML元素
const uploadForm = document.getElementById('upload-form');
const fileInput = document.getElementById('file-input');
//const thumbnailContainer = document.getElementById('thumbnail-container');
//const ticketCardId = document.getElementById('ticketCardId');
const SubmitBtn = document.querySelector('.submit');
const queryBtn = document.querySelector('.query')
const SubmitInput = document.querySelector('.submit_key');
var target_time = new Date("2023/10/31 23:59:59");
const currentTime = new Date();
SubmitBtn.onclick = async () => {
    if(SubmitInput.value && currentTime < target_time && ticketCardId.length !=0) {
        //fileObj.current_time = new Date().getTime();
        (fileObj[`${SubmitInput.value}`] = ticketCardId);
        // 向后端发送请求（使用Fetch API或其他XHR方法）
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                headers: {
                   'Content-Type': 'application/json'
                },
                body: JSON.stringify(fileObj)
            })
            .then(response => response.json())
            .then(data => {
                if (data.conflict_data){
                    console.log(data)
                    swal(`用户${data.conflict_data[0].conflict_key}存在虚假嫌疑,请举报`)
                }else {
                    swal(data)
                }
            });
            const query = await fetch('/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'text/plain'
                 },
                body: SubmitInput.value
            })
            .then(response => response.json())
            .then(data => {
                if (data.value_count){
                    swal(`你已上传${data.value_count}张月票`)
                }
            });
        } catch (error) {
            console.error('请求错误', error);
        }
    }else if(currentTime > target_time){
        swal("当前时间已经超过允许的时间范围")
    }else if (!SubmitInput.value){
        swal(`你输入的用户名为空`)
    }else{
        swal("上传内容为空")
    }
}
queryBtn.onclick = async () => {
    if(SubmitInput.value) {
        const query = await fetch('/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'text/plain'
             },
            body: SubmitInput.value
        })
        .then(response => response.json())
        .then(data => {
            if (data.value_count){
                swal(`你已上传${data.value_count}张月票`)
            }else{
                swal(`暂未查询到你上传的月票数`)
            }
        });
    }else{
        swal(`你输入的用户名为空`)
    }
}


// 添加文件上传事件监听器
uploadForm.addEventListener('change', async (e) => {
    e.preventDefault();
    
    // 获取选定的文件
    const files = fileInput.files;
    
    // 遍历选定的文件
        //ticketCardId.innerHTML = ''
    
        for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        // 创建一个FormData对象，用于向后端发送文件
        const formData = new FormData();
        formData.append('image', file);
        
        // 向后端发送请求（使用Fetch API或其他XHR方法）
        try {
            const response = await fetch('/decode_qrcode', {
                method: 'POST',
                body: formData,
            })
            .then(response => response.json())
            .then(data => {
                ticketCardId.push(...data.decoded_info)
                ticketCardId = [...new Set(ticketCardId)]
            });
            console.log(ticketCardId)
            if (ticketCardId.length ==0){
                swal("请不要拿前朝的剑来斩本朝的官!")
            }
        } catch (error) {
            console.error('请求错误', error);
        }       
    }

});



var day_ele = document.getElementById("day");
var hour_ele = document.getElementById("hour");
var min_ele = document.getElementById("min");
var sec_ele = document.getElementById("sec");

function countDown(){
    // 计算目标时间对象到当前时间的毫秒数
    var reduce_ms = target_time.getTime() - Date.now(); 
    if (reduce_ms <= 0) {
        return {
            day: 0,
            hour: 0,
            min: 0,
            sec: 0
        };
    }
    // 返回需要的数据
    return {
        day  : parseInt(reduce_ms / 1000 / 3600 / 24),
        hour : parseInt(reduce_ms / 1000 / 3600 % 24),
        min  : parseInt(reduce_ms / 1000 / 60 % 60 ),
        sec  : Math.round(reduce_ms / 1000 % 60)
    }
}


function renderCountDown(){
    var res = countDown();
    day_ele.innerHTML = addZero(res.day);
    hour_ele.innerHTML = addZero(res.hour);
    min_ele.innerHTML  = addZero(res.min);
    sec_ele.innerHTML  = addZero(res.sec);
    // 当倒计时归零时，使数字变为红色并闪烁
    if (res.day === 0 && res.hour === 0 && res.min === 0 && res.sec === 0) {
        document.getElementById('countdownTIME').style.color = "red";
        // 通过 setTimeout 来实现数字闪烁效果
        setTimeout(function () {
            document.getElementById('countdownTIME').style.color = "";
            setTimeout(renderCountDown, 1000); // 继续倒计时
        }, 500);
    } else {
        document.getElementById('countdownTIME').style.color = ""; // 恢复默认颜色
        setTimeout(renderCountDown, 1000);
    }
}

// 封装函数，当数值小于10时在前面加“0”
function addZero( num ){
    if(num < 10){
        return "0" + num;
    }
    return num;
}

// 实现倒计时效果

renderCountDown()