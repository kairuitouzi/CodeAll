function khwxfunc(jpg){
	var khwx = document.getElementById("khwx");
	var khwxbg = document.getElementById("khwxbg");
	var dis = khwx.style.display;
		if(dis=="block"){
			khwx.style.display = "none";
			khwxbg.style.display ="none";
			document.body.style.backgroundColor = "#69A1FF";
			document.body.style.opacity = 1;
		}else{
			khwxbg.style.display ="block";
			khwx.style.display = "block";
			if(jpg=="wu"){
				khwx.innerHTML = '<p style="font-size:18px;color:white;">开户微信（伍先生）</br><img src="images/wu.jpg" style="width:300px;height:300px;border:5px solid red;" title="扫码添加微信" />或手动添加微信</br>t51041</p>';
			}else if(jpg=="che"){
				khwx.innerHTML = '<p style="font-size:18px;color:white;">开户微信（车先生）</br><img src="images/che.jpg" style="width:300px;height:300px;border:5px solid red;" title="扫码添加微信" />或手动添加微信</br>kr7691</p>';
			}
		}
	}