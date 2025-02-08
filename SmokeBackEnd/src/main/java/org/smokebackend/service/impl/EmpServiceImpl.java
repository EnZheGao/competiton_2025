package org.smokebackend.service.impl;

import com.github.pagehelper.Page;
import com.github.pagehelper.PageHelper;
import org.smokebackend.mapper.EmpMapper;
import org.smokebackend.pojo.*;
import org.smokebackend.service.EmpService;

import org.smokebackend.utils.JwtUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.CollectionUtils;

import java.time.LocalDateTime;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class EmpServiceImpl implements EmpService {

    private static final Logger log = LoggerFactory.getLogger(EmpServiceImpl.class);


    @Autowired
    private EmpMapper empMapper;

    @Override
    public LoginInfo login(Emp emp) {
        Emp e = empMapper.selectByUsernameAndPassword(emp);
        if(e != null){
            log.info("登录成功：" + e);

            Map<String,Object> claims = new HashMap<>();
            claims.put("id",e.getId());
            claims.put("username",e.getUsername());
            String jwt = JwtUtils.generateJwt(claims);

            return new LoginInfo(e.getId(),e.getUsername(),e.getPassword(),jwt);
        }else{
            log.info("登录失败！");
            return null;
        }
    }
}
