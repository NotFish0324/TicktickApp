import json
import os
from datetime import datetime, timedelta

def format_ics_datetime(dt_str):
    """将 ISO 时间字符串转换为 iCalendar UTC/Local 时间格式"""
    # 兼容 "2026-10-08T14:25:00" 或 "2026-10-08"
    if 'T' in dt_str:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime('%Y%m%dT%H%M%S')
    else:
        return dt_str.replace('-', '')

def main():
    json_file = 'tasks_sync.json'
    ics_file = 'calendar.ics'

    if not os.path.exists(json_file):
        print("tasks_sync.json not found, skipping.")
        return

    with open(json_file, 'r', encoding='utf-8') as f:
        tasks = json.load(f)

    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//MyTodo GitHub Actions Sync//CN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH"
    ]

    for task in tasks:
        title = task.get('title', '未命名任务')
        due_date = task.get('dueDate')
        due_time = task.get('dueTime')
        reminder = task.get('reminder')
        priority = task.get('priority', 0) # 3=高, 0=无

        if not due_date and not reminder:
            continue

        # 确定开始时间和结束时间
        if reminder:
            dt_start_str = format_ics_datetime(reminder)
            dt_end_dt = datetime.fromisoformat(reminder) + timedelta(minutes=30)
            dt_end_str = dt_end_dt.strftime('%Y%m%dT%H%M%S')
            is_all_day = False
        elif due_time:
            full_str = f"{due_date}T{due_time}:00"
            dt_start_str = format_ics_datetime(full_str)
            dt_end_dt = datetime.fromisoformat(full_str) + timedelta(minutes=30)
            dt_end_str = dt_end_dt.strftime('%Y%m%dT%H%M%S')
            is_all_day = False
        else:
            # 全天任务
            dt_start_str = due_date.replace('-', '')
            # iCalendar 全天任务的 DTEND 需要是第二天
            next_day = datetime.fromisoformat(due_date) + timedelta(days=1)
            dt_end_str = next_day.strftime('%Y%m%d')
            is_all_day = True

        # 映射优先级 (iCalendar PRIORITY: 1=高, 5=中, 9=低)
        ics_priority = 1 if priority == 3 else 0

        ics_lines.append("BEGIN:VEVENT")
        ics_lines.append(f"UID:{task.get('id', datetime.now().timestamp())}@mytodo.github")
        ics_lines.append(f"SUMMARY:{title}")
        ics_lines.append(f"DESCRIPTION:MyTodo 待办事项同步提醒")
        
        if is_all_day:
            ics_lines.append(f"DTSTART;VALUE=DATE:{dt_start_str}")
            ics_lines.append(f"DTEND;VALUE=DATE:{dt_end_str}")
        else:
            ics_lines.append(f"DTSTART:{dt_start_str}")
            ics_lines.append(f"DTEND:{dt_end_str}")

        if ics_priority > 0:
            ics_lines.append(f"PRIORITY:{ics_priority}")

        # 添加强提醒 VALARM
        ics_lines.append("BEGIN:VALARM")
        ics_lines.append("TRIGGER:-PT0M")
        ics_lines.append("ACTION:DISPLAY")
        ics_lines.append(f"DESCRIPTION:提醒: {title}")
        ics_lines.append("END:VALARM")

        ics_lines.append("END:VEVENT")

    ics_lines.append("END:VCALENDAR")

    with open(ics_file, 'w', encoding='utf-8') as f:
        f.write("\r\n".join(ics_lines))
    print(f"Successfully generated {ics_file} with {len(tasks)} tasks.")

if __name__ == '__main__':
    main()
