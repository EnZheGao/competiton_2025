package org.smokebackend.controller;

import lombok.extern.slf4j.Slf4j;
import org.smokebackend.pojo.Emp;
import org.smokebackend.pojo.LoginInfo;
import org.smokebackend.pojo.Result;
import org.smokebackend.service.EmpService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Slf4j
@RestController
@RequestMapping("/login")
public class LoginController {

    @Autowired
    private EmpService empService;

    @PostMapping
    public Result login(@RequestBody Emp emp){
        log.info("登录:{}",emp);
        LoginInfo info = empService.login(emp);
        return info == null ? Result.error("用户名或密码错误") : Result.success(info);
    }
}
