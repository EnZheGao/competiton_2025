package org.smokebackend.pojo;

import lombok.Data;
import java.time.LocalDateTime;


@Data
public class Emp {
    private Integer id;

    private String username;
    private String password;
    private Integer job;

    private LocalDateTime createTime;
    private LocalDateTime updateTime;

}
