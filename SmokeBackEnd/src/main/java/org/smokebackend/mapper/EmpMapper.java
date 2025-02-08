package org.smokebackend.mapper;

import org.apache.ibatis.annotations.*;
import org.smokebackend.pojo.Emp;

import java.util.List;
import java.util.Map;

@Mapper
public interface EmpMapper {

    @Select("select * from emp where username = #{username} and password = #{password}")
    Emp selectByUsernameAndPassword(Emp emp);
}
