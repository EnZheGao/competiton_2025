package org.smokebackend.service;

import org.smokebackend.pojo.Emp;
import org.smokebackend.pojo.LoginInfo;

public interface EmpService {

    LoginInfo login(Emp emp);
}
