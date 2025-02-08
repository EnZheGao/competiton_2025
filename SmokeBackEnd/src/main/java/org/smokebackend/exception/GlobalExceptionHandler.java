package org.smokebackend.exception;

import lombok.extern.slf4j.Slf4j;
import org.smokebackend.pojo.Result;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler
    public Result handleException(Exception e) {
        log.error("服务器发生异常：", e);
        return Result.error("服务器发生异常：" + e.getMessage());
    }

}
