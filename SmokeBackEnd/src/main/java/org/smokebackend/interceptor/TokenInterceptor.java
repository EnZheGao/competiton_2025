package org.smokebackend.interceptor;

import io.jsonwebtoken.Claims;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.smokebackend.utils.CurrentHolder;
import org.smokebackend.utils.JwtUtils;
import org.springframework.lang.Nullable;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

@Slf4j
@Component
public class TokenInterceptor implements HandlerInterceptor {
    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {

        //获取请求头token
        String token = request.getHeader("token");
        //判断token是否存在
        if (token == null || token.isEmpty()) {
            log.info("令牌空，未登录");
            response.setStatus(401);
            return false;
        }
        //存在则校验
        try {
            Claims claims = JwtUtils.parseJWT(token);
            Integer empId = Integer.valueOf(claims.get("id").toString());
            CurrentHolder.setCurrentId(empId);
        } catch (Exception e) {
            log.info("令牌错误,无法登录");
            response.setStatus(401);
            return false;
        }
        //放行
        log.info("令牌正确");
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, @Nullable Exception ex) throws Exception {
        CurrentHolder.remove();
    }
}
